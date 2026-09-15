"""Tests for per-collection game scoping (downloads/ and installed/ subdirectories)."""
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

from dosctl.collections.factory import create_collection
from dosctl.lib import game as game_module
from dosctl.lib.game import install_game


def _make_zip(path: Path, members=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        for name, content in (members or {"GAME.EXE": "fake game"}).items():
            zf.writestr(name, content)


def _local_collection(source_dir, cache_dir, scope):
    return create_collection("local_file", str(source_dir), cache_dir, scope=scope)


def _game_archive(games_dir):
    _make_zip(games_dir / "Doom (1993)(id Software).zip")
    return "b1500715"


class TestScopePaths:
    def test_installed_dir_for_scoped_collection(self, tmp_path):
        with tempfile.TemporaryDirectory() as cache_dir:
            col = create_collection("local_file", str(tmp_path), cache_dir, scope="mine")

        assert col.installed_dir_for(Path("/base/installed")) == Path("/base/installed/mine")
        assert col.downloads_dir_for(Path("/base/downloads")) == Path("/base/downloads/mine")

    def test_unscoped_collection_keeps_flat_layout(self, tmp_path):
        with tempfile.TemporaryDirectory() as cache_dir:
            col = create_collection("local_file", str(tmp_path), cache_dir, scope=None)

        assert col.installed_dir_for(Path("/base/installed")) == Path("/base/installed")
        assert col.downloads_dir_for(Path("/base/downloads")) == Path("/base/downloads")

    def test_factory_defaults_scope_to_none(self, tmp_path):
        with tempfile.TemporaryDirectory() as cache_dir:
            col = create_collection("local_file", str(tmp_path), cache_dir)

        assert col.scope is None


class TestInstallGameScoped:
    def test_installs_into_collection_subdirectory(self, tmp_path):
        games_dir = tmp_path / "games"
        games_dir.mkdir()
        game_id = _game_archive(games_dir)

        downloads = tmp_path / "downloads"
        installed = tmp_path / "installed"
        downloads.mkdir()
        installed.mkdir()

        with tempfile.TemporaryDirectory() as cache_dir:
            col = create_collection("local_file", str(games_dir), cache_dir, scope="mine")
            with patch.object(game_module, "DOWNLOADS_DIR", downloads), \
                 patch.object(game_module, "INSTALLED_DIR", installed):
                _, install_path = install_game(col, game_id)

        assert install_path == installed / "mine" / game_id
        assert (install_path / "GAME.EXE").exists()

    def test_flat_layout_when_unscoped(self, tmp_path):
        games_dir = tmp_path / "games"
        games_dir.mkdir()
        game_id = _game_archive(games_dir)

        downloads = tmp_path / "downloads"
        installed = tmp_path / "installed"
        downloads.mkdir()
        installed.mkdir()

        with tempfile.TemporaryDirectory() as cache_dir:
            col = create_collection("local_file", str(games_dir), cache_dir)
            with patch.object(game_module, "DOWNLOADS_DIR", downloads), \
                 patch.object(game_module, "INSTALLED_DIR", installed):
                _, install_path = install_game(col, game_id)

        assert install_path == installed / game_id

    def test_two_collections_do_not_collide(self, tmp_path):
        games_dir = tmp_path / "games"
        games_dir.mkdir()
        game_id = _game_archive(games_dir)

        downloads = tmp_path / "downloads"
        installed = tmp_path / "installed"
        downloads.mkdir()
        installed.mkdir()

        with tempfile.TemporaryDirectory() as cache_a, \
             tempfile.TemporaryDirectory() as cache_b:
            col_a = create_collection("local_file", str(games_dir), cache_a, scope="a")
            col_b = create_collection("local_file", str(games_dir), cache_b, scope="b")
            with patch.object(game_module, "DOWNLOADS_DIR", downloads), \
                 patch.object(game_module, "INSTALLED_DIR", installed):
                _, path_a = install_game(col_a, game_id)
                _, path_b = install_game(col_b, game_id)

        assert path_a == installed / "a" / game_id
        assert path_b == installed / "b" / game_id
        assert path_a.exists() and path_b.exists()


class TestLegacyInstallIgnored:
    def test_flat_install_is_ignored_and_game_installs_fresh_into_scope(self, tmp_path):
        """A legacy flat-layout install is dead data: untouched, and a new
        install lands in the collection's scope."""
        games_dir = tmp_path / "games"
        games_dir.mkdir()
        game_id = _game_archive(games_dir)

        installed = tmp_path / "installed"
        legacy = installed / game_id
        legacy.mkdir(parents=True)
        (legacy / "OLD.EXE").write_text("old")
        downloads = tmp_path / "downloads"
        downloads.mkdir()

        with tempfile.TemporaryDirectory() as cache_dir:
            col = create_collection("local_file", str(games_dir), cache_dir, scope="mine")
            with patch.object(game_module, "DOWNLOADS_DIR", downloads), \
                 patch.object(game_module, "INSTALLED_DIR", installed):
                _, install_path = install_game(col, game_id)

        assert install_path == installed / "mine" / game_id
        assert (install_path / "GAME.EXE").exists()
        # The legacy directory is untouched.
        assert (legacy / "OLD.EXE").read_text() == "old"
