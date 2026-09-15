"""S3-compatible object storage collections, read over anonymous HTTPS."""

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Optional, Tuple
from urllib.parse import quote

import click
import requests
from tqdm import tqdm

from .base import CatalogCollection

_REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0"}


class S3Collection(CatalogCollection):
    """
    Zip archives in an S3-compatible bucket, reached over anonymous HTTPS.

    Works with AWS S3 and any S3-compatible store (MinIO, Backblaze B2,
    DigitalOcean Spaces, Wasabi, ...). The source URI names the bucket and an
    optional key prefix:

      s3://bucket[/prefix]                    AWS S3, virtual-host style
      s3+https://host[:port]/bucket[/prefix]  any other endpoint, path style
      s3+http://host[:port]/bucket[/prefix]   the same over plain HTTP

    The game list comes from a ListObjectsV2 request and is cached in
    games.txt in the cache directory, one tab-separated line per archive.
    """

    def __init__(self, source: str, cache_dir: str):
        base_url, bucket, prefix = self._parse_source(source)
        super().__init__(source, cache_dir, bucket)
        self.bucket = bucket
        self.prefix = prefix
        self._base_url = base_url

    @staticmethod
    def _parse_source(source: str) -> Tuple[str, str, str]:
        """
        Splits a source URI into the base URL for bucket requests, the bucket
        name and the key prefix. Raises ValueError for a URI it cannot read.
        """
        if source.startswith("s3://"):
            bucket, _, prefix = source[len("s3://"):].partition("/")
            if not bucket:
                raise ValueError(_SOURCE_ERROR.format(source=source))
            return f"https://{bucket}.s3.amazonaws.com", bucket, prefix

        if source.startswith(("s3+https://", "s3+http://")):
            scheme = source[len("s3+"):source.index("://")]
            host, _, path = source[source.index("://") + len("://"):].partition("/")
            bucket, _, prefix = path.partition("/")
            if not host or not bucket:
                raise ValueError(_SOURCE_ERROR.format(source=source))
            return f"{scheme}://{host}/{bucket}", bucket, prefix

        raise ValueError(_SOURCE_ERROR.format(source=source))

    def ensure_cache_is_present(self, force_refresh: bool = False) -> None:
        """
        Ensures the game list cache exists, listing the bucket if it's missing
        or if a refresh is forced.
        """
        cache_file = self.cache_dir / "games.txt"
        if force_refresh or not cache_file.exists():
            click.echo(f"Downloading game list from {self.source}...")
            keys = self._list_zip_keys()
            self._write_games_cache(keys, cache_file)
            click.echo("✅ Game list refreshed successfully.")

    def _list_zip_keys(self) -> List[str]:
        """Lists every .zip key in the bucket under the prefix, following pages."""
        keys: List[str] = []
        token: Optional[str] = None
        while True:
            params = {"list-type": "2"}
            if self.prefix:
                params["prefix"] = self.prefix
            if token:
                params["continuation-token"] = token
            try:
                response = requests.get(
                    f"{self._base_url}/", params=params,
                    headers=_REQUEST_HEADERS, timeout=30,
                )
                response.raise_for_status()
                token, page = self._parse_list_response(response.text)
            except (requests.exceptions.RequestException, ET.ParseError) as e:
                raise click.ClickException(f"Could not list games from {self.source}: {e}") from e
            keys.extend(page)
            if not token:
                break

        return sorted(key for key in keys if key.lower().endswith(".zip"))

    @staticmethod
    def _local_name(tag: str) -> str:
        """The tag name without its XML namespace."""
        return tag.rsplit("}", 1)[-1]

    @classmethod
    def _parse_list_response(cls, xml_text: str) -> Tuple[Optional[str], List[str]]:
        """Returns the continuation token (None when the list ends) and the keys of a page."""
        root = ET.fromstring(xml_text)
        keys = []
        for element in root.iter():
            if cls._local_name(element.tag) != "Contents":
                continue
            for child in element:
                if cls._local_name(child.tag) == "Key" and child.text:
                    keys.append(child.text)

        truncated = False
        token = None
        for child in root:
            name = cls._local_name(child.tag)
            if name == "IsTruncated":
                truncated = child.text == "true"
            elif name == "NextContinuationToken":
                token = child.text
        return (token if truncated else None), keys

    def _write_games_cache(self, keys: List[str], cache_file: Path) -> None:
        """
        Writes the keys as a pre-parsed TSV cache file.
        Each line: id<TAB>name<TAB>year<TAB>full_path
        """
        with open(cache_file, "w", encoding="utf-8") as f:
            for key in keys:
                parsed_details = self._parse_filename(Path(key).name)
                game_id = hashlib.sha1(key.encode()).hexdigest()[:8]
                year = parsed_details["year"] or ""
                f.write(f"{game_id}\t{parsed_details['name']}\t{year}\t{key}\n")

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
        """Returns the object URL for the game, or None when the ID is unknown."""
        game = self.find_game(game_id)
        if not game:
            return None
        return f"{self._base_url}/{quote(game['full_path'])}"

    def download_game(self, game_id: str, destination: str, force: bool = False) -> Optional[Path]:
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

        try:
            with requests.get(download_url, headers=_REQUEST_HEADERS, stream=True, timeout=30) as r:
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


_SOURCE_ERROR = (
    "Invalid S3 source '{source}'. Expected 's3://bucket[/prefix]' or "
    "'s3+https://host[:port]/bucket[/prefix]'."
)
