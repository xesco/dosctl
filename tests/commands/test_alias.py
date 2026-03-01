"""CLI tests for the alias command and its resolution in other commands."""
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from dosctl.main import cli


def _patch_aliases(tmp_path):
    return patch("dosctl.lib.aliases.ALIASES_FILE", tmp_path / "aliases.json")


def _make_collection(game_id="abc12345", game_name="Doom"):
    mock = MagicMock()
    mock.find_game.side_effect = lambda gid: (
        {"id": game_id, "name": game_name} if gid == game_id else None
    )
    return mock


# ---------------------------------------------------------------------------
# dosctl alias set
# ---------------------------------------------------------------------------

class TestAliasSet:
    def test_set_creates_alias(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                mock_col.return_value = _make_collection()
                result = runner.invoke(cli, ["alias", "set", "doom", "abc12345"])
        assert result.exit_code == 0
        assert "doom" in result.output
        assert "abc12345" in result.output

    def test_set_unknown_game_id_shows_error(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                mock_col.return_value = _make_collection()
                result = runner.invoke(cli, ["alias", "set", "myalias", "notfound1"])
        assert result.exit_code == 0
        assert "Error" in result.output
        assert "notfound1" in result.output

    def test_set_invalid_alias_format_shows_error(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                mock_col.return_value = _make_collection()
                result = runner.invoke(cli, ["alias", "set", "Bad_Name", "abc12345"])
        assert result.exit_code == 0
        assert "Error" in result.output

    def test_set_updates_existing_alias(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                mock_col.return_value = _make_collection()
                runner.invoke(cli, ["alias", "set", "doom", "abc12345"])
                result = runner.invoke(cli, ["alias", "set", "doom", "abc12345"])
        assert result.exit_code == 0
        assert "doom" in result.output


# ---------------------------------------------------------------------------
# dosctl alias remove
# ---------------------------------------------------------------------------

class TestAliasRemove:
    def test_remove_existing_alias(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                mock_col.return_value = _make_collection()
                runner.invoke(cli, ["alias", "set", "doom", "abc12345"])
            result = runner.invoke(cli, ["alias", "remove", "doom"])
        assert result.exit_code == 0
        assert "removed" in result.output

    def test_remove_nonexistent_alias_shows_error(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            result = runner.invoke(cli, ["alias", "remove", "doesnotexist"])
        assert result.exit_code == 0
        assert "Error" in result.output
        assert "doesnotexist" in result.output


# ---------------------------------------------------------------------------
# dosctl alias list
# ---------------------------------------------------------------------------

class TestAliasList:
    def test_list_empty(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            result = runner.invoke(cli, ["alias", "list"])
        assert result.exit_code == 0
        assert "No aliases" in result.output

    def test_list_shows_defined_aliases(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                mock_col.return_value = _make_collection()
                runner.invoke(cli, ["alias", "set", "doom", "abc12345"])
            result = runner.invoke(cli, ["alias", "list"])
        assert result.exit_code == 0
        assert "doom" in result.output
        assert "abc12345" in result.output

    def test_list_shows_multiple_aliases_sorted(self, tmp_path):
        runner = CliRunner()
        with _patch_aliases(tmp_path):
            with patch("dosctl.lib.decorators.create_collection") as mock_col:
                mock_col.return_value = _make_collection()
                runner.invoke(cli, ["alias", "set", "zork", "abc12345"])
                runner.invoke(cli, ["alias", "set", "doom", "abc12345"])
            result = runner.invoke(cli, ["alias", "list"])
        assert result.exit_code == 0
        assert result.output.index("doom") < result.output.index("zork")


# ---------------------------------------------------------------------------
# Alias resolution in other commands
# ---------------------------------------------------------------------------

class TestAliasResolutionInCommands:
    """Verify that play, inspect, delete, net host, and net join resolve aliases."""

    def _setup_alias(self, tmp_path, alias="doom", game_id="abc12345"):
        """Write an alias directly without going through the CLI."""
        f = tmp_path / "aliases.json"
        f.write_text(json.dumps({alias: game_id}))

    @patch("dosctl.commands.play.get_dosbox_launcher")
    @patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_play_resolves_alias(
        self, mock_col, mock_install, mock_dosbox, mock_launcher, tmp_path
    ):
        self._setup_alias(tmp_path)
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        with _patch_aliases(tmp_path):
            with patch("dosctl.commands.play.get_or_prompt_command", return_value="GAME.EXE"):
                with patch("dosctl.commands.play.executable_exists", return_value=True):
                    with patch("dosctl.commands.play.set_game_command"):
                        result = CliRunner().invoke(cli, ["play", "doom"])

        assert result.exit_code == 0
        called_id = mock_install.call_args[0][1]
        assert called_id == "abc12345"

    @patch("dosctl.commands.inspect.ensure_cache", lambda f: f)
    def test_inspect_resolves_alias(self, tmp_path):
        self._setup_alias(tmp_path)
        game_path = tmp_path / "abc12345"
        game_path.mkdir()
        (game_path / "DOOM.EXE").touch()

        with _patch_aliases(tmp_path):
            with patch("dosctl.commands.inspect.INSTALLED_DIR", tmp_path):
                with patch("dosctl.lib.decorators.create_collection") as mock_col:
                    mock_col.return_value = _make_collection()
                    result = CliRunner().invoke(cli, ["inspect", "doom"])

        assert result.exit_code == 0
        assert "Error" not in result.output

    @patch("dosctl.commands.delete.ensure_cache", lambda f: f)
    def test_delete_resolves_alias(self, tmp_path):
        self._setup_alias(tmp_path)
        game_path = tmp_path / "abc12345"
        game_path.mkdir()

        with _patch_aliases(tmp_path):
            with patch("dosctl.commands.delete.INSTALLED_DIR", tmp_path):
                with patch("dosctl.commands.delete.DOWNLOADS_DIR", tmp_path):
                    with patch("dosctl.lib.decorators.create_collection") as mock_col:
                        mock_col.return_value = _make_collection()
                        result = CliRunner().invoke(
                            cli, ["delete", "doom"], input="n\n"
                        )

        assert result.exit_code == 0
        # Reached the confirmation prompt — alias was resolved correctly
        assert "Doom" in result.output or "abc12345" in result.output

    @patch("dosctl.commands.net.get_dosbox_launcher")
    @patch("dosctl.commands.net.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.net.install_game")
    @patch("dosctl.commands.net.get_local_ip", return_value="192.168.1.1")
    @patch("dosctl.lib.decorators.create_collection")
    def test_net_host_resolves_alias(
        self, mock_col, mock_local_ip, mock_install, mock_dosbox, mock_launcher, tmp_path
    ):
        self._setup_alias(tmp_path)
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        with _patch_aliases(tmp_path):
            with patch("dosctl.commands.net.get_or_prompt_command", return_value="GAME.EXE"):
                with patch("dosctl.commands.net.executable_exists", return_value=True):
                    with patch("dosctl.commands.net.set_game_command"):
                        result = CliRunner().invoke(cli, ["net", "host", "doom"])

        assert result.exit_code == 0
        called_id = mock_install.call_args[0][1]
        assert called_id == "abc12345"

    @patch("dosctl.commands.net.get_dosbox_launcher")
    @patch("dosctl.commands.net.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.net.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_net_join_resolves_alias(
        self, mock_col, mock_install, mock_dosbox, mock_launcher, tmp_path
    ):
        self._setup_alias(tmp_path)
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        with _patch_aliases(tmp_path):
            with patch("dosctl.commands.net.get_or_prompt_command", return_value="GAME.EXE"):
                with patch("dosctl.commands.net.executable_exists", return_value=True):
                    with patch("dosctl.commands.net.set_game_command"):
                        result = CliRunner().invoke(
                            cli, ["net", "join", "doom", "192.168.1.42"]
                        )

        assert result.exit_code == 0
        called_id = mock_install.call_args[0][1]
        assert called_id == "abc12345"
