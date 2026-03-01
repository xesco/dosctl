"""Tests for per-game DOSBox config auto-detection."""
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from dosctl.main import cli


class TestPerGameDosboxConfig:
    """Tests that dosbox.conf in the game install dir is passed to DOSBox."""

    @patch("dosctl.commands.play.get_dosbox_launcher")
    @patch("dosctl.commands.play.get_or_prompt_command", return_value="game.exe")
    @patch("dosctl.commands.play.executable_exists", return_value=True)
    @patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_play_passes_conf_when_present(
        self, mock_collection, mock_install, mock_dosbox, mock_exists, mock_cmd, mock_launcher, tmp_path
    ):
        """play passes dosbox.conf to the launcher when it exists in the install dir."""
        game_path = tmp_path / "game"
        game_path.mkdir()
        conf_path = game_path / "dosbox.conf"
        conf_path.write_text("[cpu]\ncycles=5000\n")
        mock_install.return_value = ({}, game_path)

        runner = CliRunner()
        runner.invoke(cli, ["play", "abc12345"])

        launch_kwargs = mock_launcher.return_value.launch_game.call_args[1]
        assert launch_kwargs["conf"] == conf_path

    @patch("dosctl.commands.play.get_dosbox_launcher")
    @patch("dosctl.commands.play.get_or_prompt_command", return_value="game.exe")
    @patch("dosctl.commands.play.executable_exists", return_value=True)
    @patch("dosctl.commands.play.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.play.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_play_passes_no_conf_when_absent(
        self, mock_collection, mock_install, mock_dosbox, mock_exists, mock_cmd, mock_launcher, tmp_path
    ):
        """play passes conf=None to the launcher when no dosbox.conf exists."""
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        runner = CliRunner()
        runner.invoke(cli, ["play", "abc12345"])

        launch_kwargs = mock_launcher.return_value.launch_game.call_args[1]
        assert launch_kwargs["conf"] is None

    @patch("dosctl.commands.net._launch_net_game")
    @patch("dosctl.commands.net._prepare_game")
    @patch("dosctl.commands.net._check_dosbox", return_value=True)
    @patch("dosctl.lib.decorators.create_collection")
    def test_net_host_passes_conf_when_present(
        self, mock_collection, mock_dosbox, mock_prepare, mock_launch, tmp_path
    ):
        """net host passes dosbox.conf to the launcher when it exists."""
        game_path = tmp_path / "game"
        game_path.mkdir()
        conf_path = game_path / "dosbox.conf"
        conf_path.write_text("[cpu]\ncycles=5000\n")
        mock_prepare.return_value = (game_path, "game.exe")

        runner = CliRunner()
        runner.invoke(cli, ["net", "host", "abc12345"])

        _, kwargs = mock_launch.call_args
        assert kwargs.get("conf") == conf_path

    @patch("dosctl.commands.net._launch_net_game")
    @patch("dosctl.commands.net._prepare_game")
    @patch("dosctl.commands.net._check_dosbox", return_value=True)
    @patch("dosctl.lib.decorators.create_collection")
    def test_net_host_passes_no_conf_when_absent(
        self, mock_collection, mock_dosbox, mock_prepare, mock_launch, tmp_path
    ):
        """net host passes conf=None when no dosbox.conf exists."""
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_prepare.return_value = (game_path, "game.exe")

        runner = CliRunner()
        runner.invoke(cli, ["net", "host", "abc12345"])

        _, kwargs = mock_launch.call_args
        assert kwargs.get("conf") is None


class TestDosboxLauncherConf:
    """Tests that launch_game correctly adds -conf when the option is set."""

    def test_conf_added_to_command(self, tmp_path):
        """launch_game prepends -conf <path> when conf option is given."""
        from dosctl.lib.dosbox import StandardDOSBoxLauncher
        from dosctl.lib.platform import get_platform
        import subprocess

        game_path = tmp_path / "game"
        game_path.mkdir()
        conf_path = tmp_path / "dosbox.conf"
        conf_path.write_text("[cpu]\ncycles=5000\n")

        launcher = StandardDOSBoxLauncher(get_platform())

        with patch.object(launcher, "get_executable", return_value="dosbox"), \
             patch("subprocess.Popen") as mock_popen:
            launcher.launch_game(game_path=game_path, command=None, conf=conf_path)
            cmd = mock_popen.call_args[0][0]
            assert "-conf" in cmd
            assert str(conf_path) in cmd

    def test_no_conf_when_not_set(self, tmp_path):
        """launch_game does not add -conf when conf option is absent."""
        from dosctl.lib.dosbox import StandardDOSBoxLauncher
        from dosctl.lib.platform import get_platform

        game_path = tmp_path / "game"
        game_path.mkdir()

        launcher = StandardDOSBoxLauncher(get_platform())

        with patch.object(launcher, "get_executable", return_value="dosbox"), \
             patch("subprocess.Popen") as mock_popen:
            launcher.launch_game(game_path=game_path, command=None)
            cmd = mock_popen.call_args[0][0]
            assert "-conf" not in cmd
