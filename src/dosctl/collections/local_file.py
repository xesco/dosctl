import hashlib
from pathlib import Path
from typing import Optional

import click

from .base import CatalogCollection


class LocalFileCollection(CatalogCollection):
    """
    Zip archives in a local directory (the source), rescanned on every run.
    Archives are unpacked in place; nothing is copied to the downloads directory.
    """

    def __init__(self, source: str, cache_dir: str):
        super().__init__(source, cache_dir, "Local directory")
        self.root = Path(source).expanduser()

    def ensure_cache_is_present(self, force_refresh: bool = False) -> None:
        """Scans the directory. Reports the count when a refresh is forced."""
        self._populate_games_data()
        if force_refresh:
            click.echo(f"✅ Found {len(self._games_data)} games in '{self.root}'.")

    def _populate_games_data(self) -> None:
        if not self.root.is_dir():
            raise click.ClickException(f"Collection directory not found: '{self.root}'")

        self._games_data = []
        self._games_index = {}
        for archive in sorted(self.root.rglob("*")):
            if not archive.is_file() or archive.suffix.lower() != ".zip":
                continue
            # The relative path identifies the game, as the archive path does on Archive.org.
            full_path = archive.relative_to(self.root).as_posix()
            parsed_details = self._parse_filename(archive.name)
            self._games_data.append({
                "id": hashlib.sha1(full_path.encode()).hexdigest()[:8],
                "name": parsed_details["name"],
                "year": parsed_details["year"],
                "full_path": full_path,
            })

    def get_archive_path(self, game_id: str) -> Optional[Path]:
        """Returns the archive's path in the directory, or None for an unknown ID."""
        game = self.find_game(game_id)
        if not game:
            return None
        return self.root / game["full_path"]

    def download_game(self, game_id: str, destination: str, force: bool = False) -> Optional[Path]:
        """Returns the archive's path; copies nothing. None (with an error) if it has gone."""
        archive = self.get_archive_path(game_id)
        if archive is None:
            raise FileNotFoundError(f"Game with ID '{game_id}' not found.")

        if not archive.is_file():
            click.echo(f"Error: archive '{archive}' no longer exists.", err=True)
            return None

        return archive

    def unzip_game(self, game_id: str, download_path: Path, install_path: Path) -> None:
        """Unpacks the archive from the directory; download_path is not used."""
        archive = self.get_archive_path(game_id)
        if archive is None:
            raise FileNotFoundError(f"Game with ID '{game_id}' not found.")

        if not archive.is_file():
            raise FileNotFoundError(f"Game archive not found at '{archive}'")

        self._unpack_archive(archive, install_path)
