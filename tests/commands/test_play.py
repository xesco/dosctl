from unittest.mock import patch
from click.testing import CliRunner
from dosctl.main import cli


class TestPlayDownloadOnly:
    """Tests for the --download-only flag."""

    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_download_only_installs_without_launching(
        self, mock_collection, mock_install, tmp_path
    ):
        """--download-only should install the game and return without launching DOSBox."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        with patch("dosctl.commands.play.get_dosbox_launcher") as mock_launcher:
            result = runner.invoke(cli, ["play", "abc12345", "--download-only"])

        assert result.exit_code == 0
        mock_install.assert_called_once()
        mock_launcher.assert_not_called()

    @patch("dosctl.commands.play.is_dosbox_installed")
    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_download_only_skips_dosbox_check(
        self, mock_collection, mock_install, mock_dosbox_installed, tmp_path
    ):
        """--download-only should not check whether DOSBox is installed."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        runner.invoke(cli, ["play", "abc12345", "--download-only"])

        mock_dosbox_installed.assert_not_called()

    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_download_only_game_not_found(self, mock_collection, mock_install):
        """--download-only should show an error when the game is not found."""
        runner = CliRunner()
        mock_install.side_effect = FileNotFoundError("Game not found")

        result = runner.invoke(cli, ["play", "fake_id", "--download-only"])

        assert result.exit_code == 0
        assert "Error" in result.output
        assert "Game not found" in result.output

    @patch("dosctl.lib.decorators.create_collection")
    def test_download_only_with_no_exec_errors(self, mock_collection):
        """--download-only with --no-exec should show an error."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["play", "abc12345", "--download-only", "--no-exec"]
        )
        assert result.exit_code == 0
        assert "--download-only cannot be used with" in result.output

    @patch("dosctl.lib.decorators.create_collection")
    def test_download_only_with_configure_errors(self, mock_collection):
        """--download-only with --configure should show an error."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["play", "abc12345", "--download-only", "--configure"]
        )
        assert result.exit_code == 0
        assert "--download-only cannot be used with" in result.output

    @patch("dosctl.lib.decorators.create_collection")
    def test_download_only_with_floppy_errors(self, mock_collection):
        """--download-only with --floppy should show an error."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["play", "abc12345", "--download-only", "--floppy"]
        )
        assert result.exit_code == 0
        assert "--download-only cannot be used with" in result.output

    @patch("dosctl.lib.decorators.create_collection")
    def test_download_only_with_command_parts_errors(self, mock_collection):
        """--download-only with command arguments should show an error."""
        runner = CliRunner()
        result = runner.invoke(
            cli, ["play", "abc12345", "--download-only", "setup.exe"]
        )
        assert result.exit_code == 0
        assert "--download-only cannot be used with" in result.output

    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_download_only_short_flag(
        self, mock_collection, mock_install, tmp_path
    ):
        """Short flag -d should work the same as --download-only."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        with patch("dosctl.commands.play.get_dosbox_launcher") as mock_launcher:
            result = runner.invoke(cli, ["play", "abc12345", "-d"])

        assert result.exit_code == 0
        mock_install.assert_called_once()
        mock_launcher.assert_not_called()


@patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
@patch("dosctl.commands.play.install_game")
def test_play_command_game_not_found(mock_install_game, mock_is_installed):
    """Tests that the play command handles a missing game."""
    runner = CliRunner()
    mock_install_game.side_effect = FileNotFoundError("Game not found")

    result = runner.invoke(cli, ["play", "fake_id"])
    assert result.exit_code == 0
    assert "Error: Game not found" in result.output


class TestPlayNoExec:
    """Tests for the --no-exec flag."""

    @patch("dosctl.commands.play.get_dosbox_launcher")
    @patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_no_exec_launches_dosbox_without_command(
        self,
        mock_collection,
        mock_install,
        mock_dosbox_installed,
        mock_launcher,
        tmp_path,
    ):
        """--no-exec should launch DOSBox without running any executable."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        result = runner.invoke(cli, ["play", "abc12345", "--no-exec"])
        assert result.exit_code == 0
        assert "Opening DOSBox at game directory" in result.output

        # Verify launcher was called with command=None
        mock_launcher.return_value.launch_game.assert_called_once()
        call_kwargs = mock_launcher.return_value.launch_game.call_args[1]
        assert call_kwargs["command"] is None

    @patch("dosctl.commands.play.get_dosbox_launcher")
    @patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_no_exec_skips_executable_prompt(
        self,
        mock_collection,
        mock_install,
        mock_dosbox_installed,
        mock_launcher,
        tmp_path,
    ):
        """--no-exec should not prompt for an executable."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        with patch("dosctl.commands.play.get_or_prompt_command") as mock_prompt:
            result = runner.invoke(cli, ["play", "abc12345", "--no-exec"])
            assert result.exit_code == 0
            mock_prompt.assert_not_called()

    @patch("dosctl.commands.play.get_dosbox_launcher")
    @patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_no_exec_with_floppy(
        self,
        mock_collection,
        mock_install,
        mock_dosbox_installed,
        mock_launcher,
        tmp_path,
    ):
        """--no-exec with --floppy should mount A: drive too."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        result = runner.invoke(cli, ["play", "abc12345", "--no-exec", "--floppy"])
        assert result.exit_code == 0

        # Verify launcher was called with floppy=True and command=None
        call_kwargs = mock_launcher.return_value.launch_game.call_args[1]
        assert call_kwargs["command"] is None
        assert call_kwargs["floppy"] is True

    @patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
    @patch("dosctl.lib.decorators.create_collection")
    def test_no_exec_with_configure_errors(
        self,
        mock_collection,
        mock_dosbox_installed,
    ):
        """--no-exec with --configure should show an error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["play", "abc12345", "--no-exec", "--configure"])
        assert result.exit_code == 0
        assert "--no-exec cannot be used with --configure" in result.output

    @patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
    @patch("dosctl.lib.decorators.create_collection")
    def test_no_exec_with_command_parts_errors(
        self,
        mock_collection,
        mock_dosbox_installed,
    ):
        """--no-exec with command arguments should show an error."""
        runner = CliRunner()
        result = runner.invoke(cli, ["play", "abc12345", "--no-exec", "setup.exe"])
        assert result.exit_code == 0
        assert "--no-exec cannot be used with" in result.output

    @patch("dosctl.commands.play.get_dosbox_launcher")
    @patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_no_exec_short_flag(
        self,
        mock_collection,
        mock_install,
        mock_dosbox_installed,
        mock_launcher,
        tmp_path,
    ):
        """Short flag -n should work the same as --no-exec."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        result = runner.invoke(cli, ["play", "abc12345", "-n"])
        assert result.exit_code == 0
        assert "Opening DOSBox at game directory" in result.output
        mock_launcher.return_value.launch_game.assert_called_once()
