"""Tests for the LocalFileCollection backend."""
import hashlib
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

import click
import pytest

from dosctl.collections.factory import create_collection, get_available_collections
from dosctl.collections.local_file import LocalFileCollection
from dosctl.lib import game as game_module
from dosctl.lib.game import install_game


def _make_zip(path: Path, members=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in (members or {"GAME.EXE": "fake game"}).items():
            zf.writestr(name, content)


def _expected_id(relative_path: str) -> str:
    return hashlib.sha1(relative_path.encode()).hexdigest()[:8]


@pytest.fixture
def games_dir():
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "games"
        root.mkdir()
        _make_zip(root / "Doom (1993)(id Software).zip")
        _make_zip(root / "1990" / "Prince of Persia (1990)(Broderbund).zip")
        _make_zip(root / "SHAREWARE.ZIP")
        (root / "notes.txt").write_text("not a game")
        yield root


@pytest.fixture
def collection(games_dir):
    with tempfile.TemporaryDirectory() as cache_dir:
        yield LocalFileCollection(str(games_dir), cache_dir)


class TestLocalFileCollection:
    def test_init(self, games_dir):
        with tempfile.TemporaryDirectory() as cache_dir:
            collection = LocalFileCollection(str(games_dir), cache_dir)

        assert collection.source == str(games_dir)
        assert collection.root == games_dir
        assert collection.collection_name == "Local directory"
        assert collection._games_data == []

    def test_expands_home_in_source(self):
        with tempfile.TemporaryDirectory() as cache_dir:
            collection = LocalFileCollection("~/dos", cache_dir)

        assert collection.root == Path("~/dos").expanduser()

    def test_get_games_scans_zip_archives_recursively(self, collection):
        games = collection.get_games()

        assert [g["full_path"] for g in games] == [
            "1990/Prince of Persia (1990)(Broderbund).zip",
            "Doom (1993)(id Software).zip",
            "SHAREWARE.ZIP",
        ]

    def test_game_fields(self, collection):
        game = next(g for g in collection.get_games() if g["full_path"].startswith("1990/"))

        assert game == {
            "id": _expected_id("1990/Prince of Persia (1990)(Broderbund).zip"),
            "name": "Prince of Persia (1990)(Broderbund)",
            "year": "1990",
            "full_path": "1990/Prince of Persia (1990)(Broderbund).zip",
        }

    def test_uppercase_extension_is_stripped_and_year_is_none(self, collection):
        game = collection.find_game(_expected_id("SHAREWARE.ZIP"))

        assert game["name"] == "SHAREWARE"
        assert game["year"] is None

    def test_ensure_cache_is_present_rescans_and_writes_no_catalog(self, collection, games_dir):
        collection.ensure_cache_is_present()
        assert len(collection.get_games()) == 3

        _make_zip(games_dir / "New Game (1995).zip")
        collection.ensure_cache_is_present()

        assert len(collection.get_games()) == 4
        assert not (collection.cache_dir / "games.txt").exists()

    def test_ensure_cache_is_present_reports_count_when_forced(self, collection, capsys):
        collection.ensure_cache_is_present(force_refresh=True)

        assert capsys.readouterr().out == f"✅ Found 3 games in '{collection.root}'.\n"

    def test_ensure_cache_is_present_is_silent_by_default(self, collection, capsys):
        collection.ensure_cache_is_present()

        assert capsys.readouterr().out == ""

    def test_missing_directory_raises_click_exception(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = LocalFileCollection(str(Path(temp_dir) / "missing"), temp_dir)

            with pytest.raises(click.ClickException, match="Collection directory not found"):
                collection.ensure_cache_is_present()

    def test_find_game_unknown_id(self, collection):
        assert collection.find_game("00000000") is None

    def test_download_game_returns_archive_path_without_copying(self, collection, games_dir):
        game_id = _expected_id("Doom (1993)(id Software).zip")

        with tempfile.TemporaryDirectory() as downloads_dir:
            result = collection.download_game(game_id, downloads_dir)

            assert result == games_dir / "Doom (1993)(id Software).zip"
            assert list(Path(downloads_dir).iterdir()) == []

    def test_download_game_unknown_id(self, collection):
        with pytest.raises(FileNotFoundError, match="not found"):
            collection.download_game("00000000", "/tmp/unused")

    def test_download_game_returns_none_when_archive_removed(self, collection, games_dir, capsys):
        game_id = _expected_id("Doom (1993)(id Software).zip")
        collection.get_games()
        (games_dir / "Doom (1993)(id Software).zip").unlink()

        assert collection.download_game(game_id, "/tmp/unused") is None
        assert "no longer exists" in capsys.readouterr().err

    def test_unzip_game_unpacks_from_source_directory(self, collection):
        game_id = _expected_id("Doom (1993)(id Software).zip")

        with tempfile.TemporaryDirectory() as temp_dir:
            install_path = Path(temp_dir) / "installed" / game_id
            collection.unzip_game(game_id, Path(temp_dir) / "downloads", install_path)

            assert (install_path / "GAME.EXE").read_text() == "fake game"

    def test_unzip_game_unknown_id(self, collection):
        with pytest.raises(FileNotFoundError, match="not found"):
            collection.unzip_game("00000000", Path("/tmp"), Path("/tmp/x"))

    def test_unzip_game_rejects_unsafe_paths(self, games_dir):
        _make_zip(games_dir / "evil.zip", {"../escape.txt": "bad"})

        with tempfile.TemporaryDirectory() as cache_dir:
            collection = LocalFileCollection(str(games_dir), cache_dir)
            install_path = Path(cache_dir) / "installed" / "evil"

            with pytest.raises(ValueError, match="unsafe path"):
                collection.unzip_game(_expected_id("evil.zip"), Path(cache_dir), install_path)

            assert not install_path.exists()


class TestLocalFileFactory:
    def test_create_collection(self, games_dir):
        with tempfile.TemporaryDirectory() as cache_dir:
            collection = create_collection("local_file", str(games_dir), cache_dir)

        assert isinstance(collection, LocalFileCollection)
        assert "local_file" in get_available_collections()


class TestLocalFileInstall:
    def test_install_game_from_local_directory(self, collection):
        game_id = _expected_id("Doom (1993)(id Software).zip")

        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "downloads"
            installed_dir = Path(temp_dir) / "installed"
            downloads_dir.mkdir()
            installed_dir.mkdir()

            with patch.object(game_module, "DOWNLOADS_DIR", downloads_dir), \
                 patch.object(game_module, "INSTALLED_DIR", installed_dir):
                game, install_path = install_game(collection, game_id)

            assert game["name"] == "Doom (1993)(id Software)"
            assert install_path == installed_dir / game_id
            assert (install_path / "GAME.EXE").exists()
            assert list(downloads_dir.iterdir()) == []
