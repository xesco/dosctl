"""Tests for the inspect command."""
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from dosctl.main import cli


def _make_collection(game_id="abc12345", game_name="Doom"):
    mock = MagicMock()
    mock.find_game.side_effect = lambda gid: (
        {"id": game_id, "name": game_name} if gid == game_id else None
    )
    return mock


class TestInspectNotInstalled:
    def test_error_when_game_not_installed(self, tmp_path):
        runner = CliRunner()
        with patch("dosctl.lib.decorators.create_collection") as mock_col, \
             patch("dosctl.commands.inspect.INSTALLED_DIR", tmp_path):
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["inspect", "abc12345"])
        assert "not installed" in result.output
        assert "abc12345" in result.output


class TestInspectInstalledGame:
    def _setup_game(self, tmp_path, game_id="abc12345"):
        game_dir = tmp_path / game_id
        game_dir.mkdir()
        (game_dir / "doom.exe").write_text("exe")
        (game_dir / "readme.txt").write_text("txt")
        subdir = game_dir / "sub"
        subdir.mkdir()
        (subdir / "data.com").write_text("com")
        return game_dir

    def test_lists_all_files_with_name_and_id(self, tmp_path):
        self._setup_game(tmp_path)
        runner = CliRunner()
        with patch("dosctl.lib.decorators.create_collection") as mock_col, \
             patch("dosctl.commands.inspect.INSTALLED_DIR", tmp_path):
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["inspect", "abc12345"])
        assert "doom.exe" in result.output
        assert "readme.txt" in result.output
        assert "Doom" in result.output
        assert "abc12345" in result.output

    def test_executables_flag_filters_and_includes_subdirs(self, tmp_path):
        self._setup_game(tmp_path)
        runner = CliRunner()
        with patch("dosctl.lib.decorators.create_collection") as mock_col, \
             patch("dosctl.commands.inspect.INSTALLED_DIR", tmp_path):
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["inspect", "--executables", "abc12345"])
        assert "doom.exe" in result.output
        assert "data.com" in result.output
        assert "readme.txt" not in result.output

    def test_empty_directory_shows_no_files_message(self, tmp_path):
        (tmp_path / "abc12345").mkdir()
        runner = CliRunner()
        with patch("dosctl.lib.decorators.create_collection") as mock_col, \
             patch("dosctl.commands.inspect.INSTALLED_DIR", tmp_path):
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["inspect", "abc12345"])
        assert "No files found" in result.output

    def test_executables_flag_no_executables_shows_message(self, tmp_path):
        game_dir = tmp_path / "abc12345"
        game_dir.mkdir()
        (game_dir / "readme.txt").write_text("txt")
        runner = CliRunner()
        with patch("dosctl.lib.decorators.create_collection") as mock_col, \
             patch("dosctl.commands.inspect.INSTALLED_DIR", tmp_path):
            mock_col.return_value = _make_collection()
            result = runner.invoke(cli, ["inspect", "--executables", "abc12345"])
        assert "No executable files found" in result.output

    def test_unknown_game_id_shows_unknown_game_name(self, tmp_path):
        game_dir = tmp_path / "unknown1"
        game_dir.mkdir()
        (game_dir / "file.exe").write_text("exe")
        mock = MagicMock()
        mock.find_game.return_value = None
        runner = CliRunner()
        with patch("dosctl.lib.decorators.create_collection") as mock_col, \
             patch("dosctl.commands.inspect.INSTALLED_DIR", tmp_path):
            mock_col.return_value = mock
            result = runner.invoke(cli, ["inspect", "unknown1"])
        assert "Unknown Game" in result.output
