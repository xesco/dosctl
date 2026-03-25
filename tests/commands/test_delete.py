"""Tests for the delete command."""
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from dosctl.main import cli


def _make_collection(game_id="abc12345", game_name="Doom"):
    mock = MagicMock()
    mock.find_game.side_effect = lambda gid: (
        {"id": game_id, "name": game_name} if gid == game_id else None
    )
    return mock


def _patch_dirs(tmp_path):
    return (
        patch("dosctl.commands.delete.INSTALLED_DIR", tmp_path / "installed"),
        patch("dosctl.commands.delete.DOWNLOADS_DIR", tmp_path / "downloads"),
        patch("dosctl.lib.config_store.CONFIG_FILE", tmp_path / "play_config.json"),
        patch("dosctl.lib.aliases.ALIASES_FILE", tmp_path / "aliases.json"),
    )


class TestDeleteNotInstalled:
    def test_error_when_game_not_installed(self, tmp_path):
        p1, p2, p3, p4 = _patch_dirs(tmp_path)
        runner = CliRunner()
        with p1, p2, p3, p4, patch("dosctl.lib.decorators.create_collection") as mock_col:
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["delete", "abc12345"])
        assert "not installed" in result.output
        assert "abc12345" in result.output


class TestDeleteCancelled:
    def test_cancellation_aborts_deletion(self, tmp_path):
        installed = tmp_path / "installed"
        installed.mkdir()
        game_dir = installed / "abc12345"
        game_dir.mkdir()
        (game_dir / "doom.exe").write_text("exe")

        p1, p2, p3, p4 = _patch_dirs(tmp_path)
        runner = CliRunner()
        with p1, p2, p3, p4, patch("dosctl.lib.decorators.create_collection") as mock_col:
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["delete", "abc12345"], input="n\n")
        assert game_dir.exists()
        assert "cancelled" in result.output.lower()


class TestDeleteSuccess:
    def _setup(self, tmp_path, game_id="abc12345"):
        installed = tmp_path / "installed"
        installed.mkdir()
        (tmp_path / "downloads").mkdir()
        game_dir = installed / game_id
        game_dir.mkdir()
        (game_dir / "doom.exe").write_text("exe")
        return game_dir

    def test_deletes_installation_directory(self, tmp_path):
        game_dir = self._setup(tmp_path)
        p1, p2, p3, p4 = _patch_dirs(tmp_path)
        runner = CliRunner()
        with p1, p2, p3, p4, patch("dosctl.lib.decorators.create_collection") as mock_col:
            mock_col.return_value = _make_collection()
            runner.invoke(cli, ["delete", "abc12345"], input="y\n")
        assert not game_dir.exists()

    def test_deletes_downloaded_zip_when_present(self, tmp_path):
        self._setup(tmp_path)
        zip_file = tmp_path / "downloads" / "Doom.zip"
        zip_file.write_bytes(b"zip")
        p1, p2, p3, p4 = _patch_dirs(tmp_path)
        runner = CliRunner()
        with p1, p2, p3, p4, patch("dosctl.lib.decorators.create_collection") as mock_col:
            mock_col.return_value = _make_collection()
            runner.invoke(cli, ["delete", "abc12345"], input="y\n")
        assert not zip_file.exists()

    def test_removes_saved_command(self, tmp_path):
        self._setup(tmp_path)
        (tmp_path / "play_config.json").write_text(json.dumps({"abc12345": "doom.exe"}))
        p1, p2, p3, p4 = _patch_dirs(tmp_path)
        runner = CliRunner()
        with p1, p2, p3, p4, patch("dosctl.lib.decorators.create_collection") as mock_col:
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["delete", "abc12345"], input="y\n")
        assert "Removed saved launch command" in result.output
        assert "abc12345" not in json.loads((tmp_path / "play_config.json").read_text())

    def test_removes_aliases(self, tmp_path):
        self._setup(tmp_path)
        (tmp_path / "aliases.json").write_text(
            json.dumps({"doom": {"id": "abc12345", "name": "Doom"}})
        )
        p1, p2, p3, p4 = _patch_dirs(tmp_path)
        runner = CliRunner()
        with p1, p2, p3, p4, patch("dosctl.lib.decorators.create_collection") as mock_col:
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["delete", "abc12345"], input="y\n")
        assert "doom" in result.output
        assert "doom" not in json.loads((tmp_path / "aliases.json").read_text())

    def test_shows_game_name_in_prompt(self, tmp_path):
        self._setup(tmp_path)
        p1, p2, p3, p4 = _patch_dirs(tmp_path)
        runner = CliRunner()
        with p1, p2, p3, p4, patch("dosctl.lib.decorators.create_collection") as mock_col:
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["delete", "abc12345"], input="y\n")
        assert "Doom" in result.output
