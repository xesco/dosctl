import re
import shutil
import subprocess
import tempfile
import zipfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional

import click

# Compression methods zipfile can read: stored, deflate, bzip2 and lzma.
_PYTHON_ZIP_METHODS = {
    zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED, zipfile.ZIP_BZIP2, zipfile.ZIP_LZMA,
}


class BaseCollection(ABC):
    """
    Abstract base class for a game collection.
    """
    def __init__(self, source: str):
        self.source = source
        # Name of the subdirectory of downloads/ and installed/ that holds this
        # collection's games; None keeps the legacy flat layout.
        self.scope = None

    def installed_dir_for(self, base: Path) -> Path:
        """The directory where this collection's installed games live under base."""
        return base / self.scope if self.scope else base

    def downloads_dir_for(self, base: Path) -> Path:
        """The directory where this collection's downloaded archives live under base."""
        return base / self.scope if self.scope else base

    @abstractmethod
    def load(self) -> None:
        pass

    @abstractmethod
    def get_games(self) -> List[Dict]:
        pass

    @abstractmethod
    def download_game(self, game_name: str, destination: str) -> None:
        pass


class CatalogCollection(BaseCollection):
    """
    A collection of zip archives held in an in-memory list.
    Subclasses build the list and fetch archives; lookup and unpacking live here.
    """

    def __init__(self, source: str, cache_dir: str, collection_name: str):
        super().__init__(source)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self._games_data: List[Dict] = []
        self._games_index: Dict[str, Dict] = {}

    @abstractmethod
    def ensure_cache_is_present(self, force_refresh: bool = False) -> None:
        """Makes the list of games available."""

    @abstractmethod
    def _populate_games_data(self) -> None:
        """Fills _games_data."""

    def load(self, force_refresh: bool = False) -> None:
        self.ensure_cache_is_present(force_refresh=force_refresh)
        self._populate_games_data()

    def _parse_filename(self, filename: str) -> Dict:
        """
        Parses a filename to extract the year and a clean name.
        Can be overridden by subclasses for different parsing logic.
        """
        name_part = re.sub(r'\.zip$', '', filename, flags=re.IGNORECASE)
        year = None

        # Try to find a year like (1995) in the name
        match = re.search(r'\(([0-9]{4})\)', name_part)
        if match:
            year = match.group(1)

        return {"name": name_part, "year": year}

    def get_games(self) -> List[Dict]:
        if not self._games_data:
            self._populate_games_data()
        return self._games_data

    def _ensure_index(self) -> None:
        """(Re)build the id->game index when it is out of sync with _games_data."""
        if len(self._games_index) != len(self._games_data):
            self._games_index = {game["id"]: game for game in self._games_data}

    def find_game(self, game_id: str) -> Optional[Dict]:
        if not self._games_data:
            self._populate_games_data()
        self._ensure_index()
        return self._games_index.get(game_id)

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

        self._unpack_archive(zip_filepath, install_path)

    def _unpack_archive(self, zip_filepath: Path, install_path: Path) -> None:
        click.echo(f"Unzipping '{zip_filepath.name}' to '{install_path}'...")
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            self._extract_zip_safely(zip_ref, install_path)
        click.echo("Unzip complete.")

    def _extract_zip_safely(self, zip_ref: zipfile.ZipFile, install_path: Path) -> None:
        """Extract a ZIP into the install path without allowing path escapes.

        Files are extracted into a sibling temporary directory first and only
        moved into place after the whole archive has been validated and
        extracted successfully.
        """
        install_parent = install_path.parent
        install_parent.mkdir(parents=True, exist_ok=True)

        temp_install_path = Path(
            tempfile.mkdtemp(prefix=f"{install_path.name}.tmp-", dir=str(install_parent))
        )

        try:
            members = zip_ref.infolist()
            targets = [
                self._validated_extract_path(m.filename, install_root=temp_install_path)
                for m in members
            ]

            if self._needs_external_unzip(members):
                self._extract_with_unzip(Path(zip_ref.filename), temp_install_path)
            else:
                self._extract_members(zip_ref, members, targets)

            temp_install_path.rename(install_path)
        except Exception:
            shutil.rmtree(temp_install_path, ignore_errors=True)
            raise

    def _extract_members(self, zip_ref: zipfile.ZipFile, members, targets) -> None:
        for member, target_path in zip(members, targets):
            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue

            target_path.parent.mkdir(parents=True, exist_ok=True)
            with zip_ref.open(member, "r") as source, open(target_path, "wb") as dest:
                shutil.copyfileobj(source, dest)

    def _needs_external_unzip(self, members) -> bool:
        """True when a member uses a method zipfile cannot read, e.g. PKZIP 1.x Implode."""
        return any(m.compress_type not in _PYTHON_ZIP_METHODS for m in members)

    def _extract_with_unzip(self, zip_filepath: Path, target_dir: Path) -> None:
        unzip = shutil.which("unzip")
        if not unzip:
            raise RuntimeError(
                f"'{zip_filepath.name}' uses a compression method Python cannot read "
                "and the 'unzip' command is not installed."
            )
        result = subprocess.run(
            [unzip, "-qq", "-o", str(zip_filepath), "-d", str(target_dir)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
        )
        # Info-ZIP exits 1 for warnings after a complete extraction.
        if result.returncode > 1:
            raise RuntimeError(f"unzip failed on '{zip_filepath.name}': {result.stderr.strip()}")

    def _validated_extract_path(self, member_name: str, install_root: Path) -> Path:
        """Return the validated extraction target for a ZIP member."""
        normalized_name = member_name.replace("\\", "/")

        if not normalized_name or normalized_name.startswith("/"):
            raise ValueError(f"Archive contains an unsafe path: '{member_name}'")

        if re.match(r"^[A-Za-z]:", normalized_name):
            raise ValueError(f"Archive contains an unsafe path: '{member_name}'")

        member_path = Path(normalized_name)
        if any(part in ("", ".", "..") for part in member_path.parts):
            raise ValueError(f"Archive contains an unsafe path: '{member_name}'")

        return install_root.joinpath(*member_path.parts)
