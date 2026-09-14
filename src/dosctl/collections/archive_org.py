import hashlib
import re
from pathlib import Path
from typing import Optional
from urllib.parse import quote, unquote

import click
import requests
from tqdm import tqdm

from .base import CatalogCollection


class ArchiveOrgCollection(CatalogCollection):
    """
    Base class for Archive.org collection backends.
    Handles common functionality like downloading, caching, and parsing.
    """

    def __init__(self, source: str, cache_dir: str, collection_name: str):
        super().__init__(source, cache_dir, collection_name)

        # The download URL for a file is different from the source URL of the list.
        # We derive the base download URL from the source URL's item name.
        # e.g., https://.../items/ITEM_NAME/file.txt -> https://archive.org/download/ITEM_NAME
        self.item_name = self.source.split("/")[-2]
        self.download_base_url = f"https://archive.org/download/{self.item_name}"

    def ensure_cache_is_present(self, force_refresh: bool = False) -> None:
        """
        Ensures the game list cache exists, downloading it if it's missing or
        if a refresh is forced.
        """
        cache_file = self.cache_dir / "games.txt"
        if force_refresh or not cache_file.exists():
            click.echo(f"Downloading game list from {self.source}...")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.source, headers=headers, timeout=30)
            response.raise_for_status()
            self._build_games_cache(response.text, cache_file)
            click.echo("✅ Game list refreshed successfully.")

    def _build_games_cache(self, html_content: str, cache_file: Path) -> None:
        """
        Parses HTML content from Archive.org and writes a pre-parsed TSV cache file.
        Each line: id<TAB>name<TAB>year<TAB>full_path
        """
        zip_hrefs = re.findall(r'href="(.+?\.zip)"', html_content)

        with open(cache_file, "w", encoding="utf-8") as f:
            for href in zip_hrefs:
                encoded_path = href.split("/")[-1]
                full_path = unquote(encoded_path)
                filename_with_ext = Path(full_path).name
                parsed_details = self._parse_filename(filename_with_ext)
                game_hash = hashlib.sha1(full_path.encode()).hexdigest()
                game_id = game_hash[:8]
                year = parsed_details["year"] or ""
                f.write(f"{game_id}\t{parsed_details['name']}\t{year}\t{full_path}\n")

    def _populate_games_data(self) -> None:
        cache_file = self.cache_dir / "games.txt"
        if not cache_file.exists():
            return

        self._games_data = []
        self._games_index = {}
        with open(cache_file, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line:
                    continue
                parts = line.split("\t")
                if len(parts) != 4:
                    continue
                game_id, name, year, full_path = parts
                self._games_data.append({
                    "id": game_id,
                    "name": name,
                    "year": year if year else None,
                    "full_path": full_path,
                })

    def get_download_url(self, game_id: str) -> Optional[str]:
        """
        Constructs the download URL for a specific game.
        Can be overridden by subclasses for different URL patterns.
        """
        game = self.find_game(game_id)
        if not game:
            return None

        # The download URL is constructed from the base item name and the full path
        encoded_full_path = quote(game["full_path"])
        return self._build_download_url(encoded_full_path)

    def _build_download_url(self, encoded_full_path: str) -> str:
        """
        Builds the actual download URL. Override this in subclasses for different URL patterns.
        """
        raise NotImplementedError("Subclasses must implement _build_download_url")

    def download_game(self, game_id: str, destination: str, force: bool = False) -> None:
        download_url = self.get_download_url(game_id)
        if not download_url:
            raise FileNotFoundError(f"Game with ID '{game_id}' not found.")

        game = self.find_game(game_id)
        destination_path = Path(destination)
        destination_path.mkdir(parents=True, exist_ok=True)

        filename = game["name"] + ".zip"
        local_zip_path = destination_path / filename

        if local_zip_path.exists() and not force:
            click.echo(f"'{filename}' already exists in '{destination_path}'. Use --force to overwrite.")
            return local_zip_path

        headers = {'User-Agent': 'Mozilla/5.0'}

        try:
            with requests.get(download_url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()

                total_size = int(r.headers.get('content-length', 0))

                bytes_written = 0
                with tqdm.wrapattr(open(local_zip_path, "wb"), "write",
                                 miniters=1,
                                 total=total_size,
                                 desc=f"Downloading '{filename}'") as fout:
                    for chunk in r.iter_content(chunk_size=8192):
                        fout.write(chunk)
                        bytes_written += len(chunk)

            # Verify the transfer is complete. A dropped connection can end the
            # stream early, leaving a truncated (corrupt) zip that still looks
            # like a valid file on disk; reject it instead of "installing" it.
            if total_size and bytes_written < total_size:
                raise OSError(
                    f"incomplete download: expected {total_size} bytes, "
                    f"got {bytes_written}"
                )

            click.echo(f"Successfully downloaded '{filename}'")
        except (requests.exceptions.RequestException, OSError) as e:
            click.echo(f"\nError downloading '{filename}': {e}", err=True)
            # Clean up the partially downloaded file
            local_zip_path.unlink(missing_ok=True)
            return None
        except BaseException:
            # Clean up the partial file on interrupt (e.g. Ctrl-C) before re-raising
            local_zip_path.unlink(missing_ok=True)
            raise

        return local_zip_path


class TotalDOSCollectionRelease14(ArchiveOrgCollection):
    """
    Specific implementation for Total DOS Collection Release 14.
    """

    def __init__(self, source: str, cache_dir: str):
        super().__init__(source, cache_dir, "Total DOS Collection Release 14")

    def _build_download_url(self, encoded_full_path: str) -> str:
        """
        Builds the download URL specific to TDC Release 14 structure.
        """
        return f"https://archive.org/download/{self.item_name}/TDC_Release_14.zip/{encoded_full_path}"
