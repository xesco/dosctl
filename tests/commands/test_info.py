"""Tests for the info command."""
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from dosctl.main import cli


GAME = {"id": "abc12345", "name": "Doom (1993)", "year": "1993", "full_path": "Doom (1993).zip"}


def _make_collection(game=GAME):
    mock = MagicMock()
    mock.find_game.side_effect = lambda gid: game if gid == game["id"] else None
    return mock


def _patch_aliases(tmp_path, aliases=None):
    f = tmp_path / "aliases.json"
    f.write_text(json.dumps(aliases or {}))
    return patch("dosctl.lib.aliases.ALIASES_FILE", f)


# ---------------------------------------------------------------------------
# Basic output
# ---------------------------------------------------------------------------

class TestInfoCommand:
    def test_shows_name_id_year(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", tmp_path / "installed"):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", tmp_path / "downloads"):
                        with patch("dosctl.commands.info.get_game_command", return_value=None):
                            mock_col.return_value = _make_collection()
                            result = runner.invoke(cli, ["info", "abc12345"])

        assert result.exit_code == 0
        assert "Doom (1993)" in result.output
        assert "abc12345" in result.output
        assert "1993" in result.output

    def test_unknown_game_id_shows_error(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                mock_col.return_value = _make_collection()
                result = runner.invoke(cli, ["info", "notfound"])

        assert result.exit_code == 0
        assert "Error" in result.output

    def test_game_with_no_year_shows_placeholder(self, tmp_path):
        game = {**GAME, "year": None}
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", tmp_path / "installed"):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", tmp_path / "downloads"):
                        with patch("dosctl.commands.info.get_game_command", return_value=None):
                            mock_col.return_value = _make_collection(game)
                            result = runner.invoke(cli, ["info", "abc12345"])

        assert result.exit_code == 0
        assert "----" in result.output


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------

class TestInfoStatus:
    def test_status_not_downloaded(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", tmp_path / "installed"):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", tmp_path / "downloads"):
                        with patch("dosctl.commands.info.get_game_command", return_value=None):
                            mock_col.return_value = _make_collection()
                            result = runner.invoke(cli, ["info", "abc12345"])

        assert "Not downloaded" in result.output
        assert "Archive:" not in result.output
        assert "Path:" not in result.output

    def test_status_downloaded(self, tmp_path):
        downloads = tmp_path / "downloads"
        downloads.mkdir()
        (downloads / "Doom (1993).zip").touch()

        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", tmp_path / "installed"):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", downloads):
                        with patch("dosctl.commands.info.get_game_command", return_value=None):
                            mock_col.return_value = _make_collection()
                            result = runner.invoke(cli, ["info", "abc12345"])

        assert "Downloaded" in result.output
        assert "Archive:" in result.output
        assert "Path:" not in result.output

    def test_status_installed(self, tmp_path):
        installed = tmp_path / "installed"
        (installed / "abc12345").mkdir(parents=True)

        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", installed):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", tmp_path / "downloads"):
                        with patch("dosctl.commands.info.get_game_command", return_value=None):
                            mock_col.return_value = _make_collection()
                            result = runner.invoke(cli, ["info", "abc12345"])

        assert "Installed" in result.output
        assert "Path:" in result.output
        assert "Archive:" not in result.output


# ---------------------------------------------------------------------------
# Alias and command
# ---------------------------------------------------------------------------

class TestInfoAliasAndCommand:
    def test_shows_alias_when_set(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path, {"doom": {"id": "abc12345", "name": "Doom (1993)"}}):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", tmp_path / "installed"):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", tmp_path / "downloads"):
                        with patch("dosctl.commands.info.get_game_command", return_value=None):
                            mock_col.return_value = _make_collection()
                            result = runner.invoke(cli, ["info", "abc12345"])

        assert "Alias:" in result.output
        assert "doom" in result.output

    def test_omits_alias_line_when_none(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", tmp_path / "installed"):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", tmp_path / "downloads"):
                        with patch("dosctl.commands.info.get_game_command", return_value=None):
                            mock_col.return_value = _make_collection()
                            result = runner.invoke(cli, ["info", "abc12345"])

        assert "Alias:" not in result.output

    def test_shows_saved_command(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", tmp_path / "installed"):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", tmp_path / "downloads"):
                        with patch("dosctl.commands.info.get_game_command", return_value="DOOM.EXE"):
                            mock_col.return_value = _make_collection()
                            result = runner.invoke(cli, ["info", "abc12345"])

        assert "Command:" in result.output
        assert "DOOM.EXE" in result.output

    def test_omits_command_line_when_none(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", tmp_path / "installed"):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", tmp_path / "downloads"):
                        with patch("dosctl.commands.info.get_game_command", return_value=None):
                            mock_col.return_value = _make_collection()
                            result = runner.invoke(cli, ["info", "abc12345"])

        assert "Command:" not in result.output

    def test_resolves_alias_as_argument(self, tmp_path):
        """Passing an alias instead of a raw ID should work."""
        runner = CliRunner()
        with _patch_aliases(tmp_path, {"doom": {"id": "abc12345", "name": "Doom (1993)"}}):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                with patch("dosctl.commands.info.INSTALLED_DIR", tmp_path / "installed"):
                    with patch("dosctl.commands.info.DOWNLOADS_DIR", tmp_path / "downloads"):
                        with patch("dosctl.commands.info.get_game_command", return_value=None):
                            mock_col.return_value = _make_collection()
                            result = runner.invoke(cli, ["info", "doom"])

        assert result.exit_code == 0
        assert "Doom (1993)" in result.output
        assert "abc12345" in result.output
