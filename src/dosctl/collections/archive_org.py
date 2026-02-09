import hashlib
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional
import zipfile
from urllib.parse import quote, unquote
from tqdm import tqdm

from .base import BaseCollection

class ArchiveOrgCollection(BaseCollection):
    """
    Base class for Archive.org collection backends.
    Handles common functionality like downloading, caching, and parsing.
    """

    def __init__(self, source: str, cache_dir: str, collection_name: str):
        super().__init__(source)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self._games_data: List[Dict] = []

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
            print(f"Downloading game list from {self.source}...")
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(self.source, headers=headers, timeout=30)
            response.raise_for_status()
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            print("✅ Game list refreshed successfully.")

    def load(self, force_refresh: bool = False) -> None:
        self.ensure_cache_is_present(force_refresh=force_refresh)
        self._populate_games_data()

    def _parse_filename(self, filename: str) -> Dict:
        """
        Parses a filename to extract the year and a clean name.
        Can be overridden by subclasses for different parsing logic.
        """
        name_part = filename.replace(".zip", "")
        year = None

        # Try to find a year like (1995) in the name
        match = re.search(r'\(([0-9]{4})\)', name_part)
        if match:
            year = match.group(1)

        return {"name": name_part, "year": year}

    def _populate_games_data(self) -> None:
        cache_file = self.cache_dir / "games.txt"
        if not cache_file.exists():
            return

        self._games_data = []
        with open(cache_file, "r", encoding="utf-8") as f:
            content = f.read()

        zip_hrefs = re.findall(r'href="(.+?\.zip)"', content)

        for href in zip_hrefs:
            encoded_path = href.split("/")[-1]
            full_path = unquote(encoded_path)

            filename_with_ext = Path(full_path).name

            # Use the parser (can be overridden by subclasses)
            parsed_details = self._parse_filename(filename_with_ext)

            # The game's unique ID is a short, stable hash of its full path.
            # This prevents collisions and ensures the ID is always the same.
            game_hash = hashlib.sha1(full_path.encode()).hexdigest()
            game_id = game_hash[:8]

            self._games_data.append({
                "id": game_id,
                "name": parsed_details["name"],
                "year": parsed_details["year"],
                "full_path": full_path,
            })

    def get_games(self) -> List[Dict]:
        if not self._games_data:
            self._populate_games_data()
        return self._games_data

    def find_game(self, game_id: str) -> Optional[Dict]:
        if not self._games_data:
            self._populate_games_data()
        for game in self._games_data:
            if game["id"] == game_id:
                return game
        return None

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
            print(f"'{filename}' already exists in '{destination_path}'. Use --force to overwrite.")
            return local_zip_path

        headers = {'User-Agent': 'Mozilla/5.0'}

        # Use a try...except block for more specific error handling
        try:
            with requests.get(download_url, headers=headers, stream=True, timeout=30) as r:
                r.raise_for_status()

                total_size = int(r.headers.get('content-length', 0))

                with tqdm.wrapattr(open(local_zip_path, "wb"), "write",
                                 miniters=1,
                                 total=total_size,
                                 desc=f"Downloading '{filename}'") as fout:
                    for chunk in r.iter_content(chunk_size=8192):
                        fout.write(chunk)

            print(f"Successfully downloaded '{filename}'")
        except requests.exceptions.RequestException as e:
            print(f"\nError downloading '{filename}': {e}")
            # Clean up partially downloaded file
            if local_zip_path.exists():
                local_zip_path.unlink()
            return None

        return local_zip_path

    def unzip_game(self, game_id: str, download_path: Path, install_path: Path) -> None:
        """
        Unzips a downloaded game to a specified installation directory.
        """
        game = self.find_game(game_id)
        if not game:
            raise FileNotFoundError(f"Game with ID '{game_id}' not found.")

        zip_filename = game["name"] + ".zip"
        zip_filepath = download_path / zip_filename

        if not zip_filepath.exists():
            raise FileNotFoundError(f"Downloaded game zip not found at '{zip_filepath}'")

        print(f"Unzipping '{zip_filename}' to '{install_path}'...")
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            zip_ref.extractall(install_path)
        print("Unzip complete.")


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


# Example of how to add a new version:
#
# class TotalDOSCollectionRelease15(ArchiveOrgCollection):
#     """
#     Specific implementation for Total DOS Collection Release 15.
#     """
#
#     def __init__(self, source: str, cache_dir: str):
#         super().__init__(source, cache_dir, "Total DOS Collection Release 15")
#
#     def _build_download_url(self, encoded_full_path: str) -> str:
#         """
#         Builds the download URL specific to TDC Release 15 structure.
#         """
#         return f"https://archive.org/download/{self.item_name}/TDC_Release_15.zip/{encoded_full_path}"
#
#     def _parse_filename(self, filename: str) -> Dict:
#         """
#         Override if Release 15 has different filename patterns.
#         """
#         # Custom parsing logic for Release 15 if needed
#         return super()._parse_filename(filename)
