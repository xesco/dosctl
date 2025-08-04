import hashlib
import re
import requests
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import quote

from .base import BaseCollection

class ArchiveOrgCollection(BaseCollection):
    """
    A collection backend for games stored on archive.org.
    """

    def __init__(self, source: str, cache_dir: str):
        super().__init__(source)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._games_data: List[Dict] = []
        # The download URL is based on the item name, derived from the source
        self.item_name = self.source.split("/")[-2]
        self.download_base_url = f"https://archive.org/download/{self.item_name}"

    def load(self, force_refresh: bool = False) -> None:
        """
        Loads the game list by downloading the plain text file.
        """
        cache_file = self.cache_dir / "games.txt"
        if force_refresh or not cache_file.exists():
            print(f"Downloading game list from {self.source}...")
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
            }
            response = requests.get(self.source, headers=headers)
            response.raise_for_status()
            
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(response.text)
        
        self._populate_games_data()

    def _populate_games_data(self) -> None:
        """
        Parses the cached games.txt file to build the internal games list.
        """
        cache_file = self.cache_dir / "games.txt"
        if not cache_file.exists():
            return

        self._games_data = []
        with open(cache_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line.endswith('.zip'):
                    continue
                
                # Extract the full path from the line
                match = re.search(r'TDC release 13\\.+', line)
                if not match:
                    continue
                
                full_path = match.group(0)
                filename = Path(full_path).name
                
                game_hash = hashlib.sha1(filename.encode()).hexdigest()
                game_id = game_hash[:4]
                
                details = self._parse_filename(filename)
                
                self._games_data.append({
                    "id": game_id,
                    "name": details["name"],
                    "year": details["year"],
                    "filename": filename,
                    "full_path": full_path,
                })

    def get_games(self, sort_by: str = 'name') -> List[Dict]:
        if not self._games_data:
            self._populate_games_data()
        return self._games_data

    def _find_game(self, game_id: str) -> Optional[Dict]:
        if not self._games_data:
            self._populate_games_data()
        for game in self._games_data:
            if game["id"] == game_id:
                return game
        return None

    def _parse_filename(self, filename: str) -> Dict:
        name_part = filename
        if name_part.endswith('.zip'):
            name_part = name_part[:-4]

        details = {
            "verified": False, "genre": None, "publisher": None, "year": None,
            "tags": [], "languages": [], "qualifiers": [], "name": ""
        }

        if name_part.endswith('[!]'):
            details['verified'] = True
            name_part = name_part[:-3].strip()

        genre_match = re.search(r'\[([^\]]+)\]$', name_part)
        if genre_match:
            details['genre'] = genre_match.group(1)
            name_part = name_part[:genre_match.start()].strip()

            pub_match = re.search(r'\(([^)]+)\)$', name_part)
            if pub_match:
                details['publisher'] = pub_match.group(1)
                name_part = name_part[:pub_match.start()].strip()

            year_match = re.search(r'\(([0-9]{4}|19xx|199x)\)$', name_part)
            if year_match:
                year_str = year_match.group(1)
                details['year'] = year_str if 'x' in year_str else int(year_str)
                name_part = name_part[:year_match.start()].strip()

        while True:
            tag_match = re.search(r'\[([^\]]+)\]$', name_part)
            if tag_match:
                details['tags'].insert(0, tag_match.group(1))
                name_part = name_part[:tag_match.start()].strip()
                continue

            lang_qual_match = re.search(r'\(([^)]+)\)$', name_part)
            if lang_qual_match:
                content = lang_qual_match.group(1)
                if re.fullmatch(r'[A-Z][a-z](-[A-Z]{2})?', content):
                    details['languages'].insert(0, content)
                else:
                    details['qualifiers'].insert(0, content)
                name_part = name_part[:lang_qual_match.start()].strip()
                continue
            
            break

        if not details['languages']:
            details['languages'].append('En')

        details['name'] = name_part.strip()
        return details

    def get_game_details(self, game_id: str) -> Dict:
        game = self._find_game(game_id)
        if not game:
            return {}

        details = self._parse_filename(game["filename"])
        details["id"] = game["id"]
        details["filename"] = game["filename"]
        details["full_path"] = game["full_path"]
        return details

    def get_download_url(self, game_id: str) -> Optional[str]:
        game = self._find_game(game_id)
        if not game:
            return None
        
        # The path in the text file uses backslashes, which need to be
        # replaced with forward slashes for the URL.
        path_with_forward_slashes = game["full_path"].replace(r"\\", "/")
        encoded_full_path = quote(path_with_forward_slashes)
        return f"{self.download_base_url}/{encoded_full_path}"

    def download_game(self, game_id: str, destination: str) -> None:
        download_url = self.get_download_url(game_id)
        if not download_url:
            raise FileNotFoundError(f"Game with ID '{game_id}' not found.")

        destination_path = Path(destination)
        destination_path.mkdir(parents=True, exist_ok=True)
        
        game_filename = self._find_game(game_id)["filename"]
        local_zip_path = destination_path / game_filename

        print(f"Downloading '{game_filename}'...")
        headers = {
            'User-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        }
        response = requests.get(download_url, headers=headers, stream=True)
        response.raise_for_status()

        with open(local_zip_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded to '{local_zip_path}'")
