"""Tests for the net command (IPX multiplayer networking)."""

from pathlib import Path
from unittest.mock import patch, MagicMock, call
from click.testing import CliRunner
from dosctl.main import cli
from dosctl.lib.network import (
    IPXServerConfig,
    IPXClientConfig,
    DEFAULT_IPX_PORT,
    get_local_ip,
)


# --- Network dataclass tests ---


class TestIPXServerConfig:
    """Test IPXServerConfig dataclass."""

    def test_default_port(self):
        config = IPXServerConfig()
        assert config.port == DEFAULT_IPX_PORT

    def test_custom_port(self):
        config = IPXServerConfig(port=12345)
        assert config.port == 12345

    def test_to_dosbox_command_default_port(self):
        config = IPXServerConfig()
        assert config.to_dosbox_command() == f"IPXNET STARTSERVER {DEFAULT_IPX_PORT}"

    def test_to_dosbox_command_custom_port(self):
        config = IPXServerConfig(port=9999)
        assert config.to_dosbox_command() == "IPXNET STARTSERVER 9999"


class TestIPXClientConfig:
    """Test IPXClientConfig dataclass."""

    def test_default_port(self):
        config = IPXClientConfig(host="192.168.1.42")
        assert config.host == "192.168.1.42"
        assert config.port == DEFAULT_IPX_PORT

    def test_custom_port(self):
        config = IPXClientConfig(host="10.0.0.1", port=12345)
        assert config.host == "10.0.0.1"
        assert config.port == 12345

    def test_to_dosbox_command_default_port(self):
        config = IPXClientConfig(host="192.168.1.42")
        assert (
            config.to_dosbox_command()
            == f"IPXNET CONNECT 192.168.1.42 {DEFAULT_IPX_PORT}"
        )

    def test_to_dosbox_command_custom_port(self):
        config = IPXClientConfig(host="10.0.0.1", port=9999)
        assert config.to_dosbox_command() == "IPXNET CONNECT 10.0.0.1 9999"


class TestGetLocalIP:
    """Test get_local_ip function."""

    @patch("dosctl.lib.network.socket.socket")
    def test_returns_ip_on_success(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket.getsockname.return_value = ("192.168.1.100", 0)
        mock_socket_class.return_value = mock_socket

        result = get_local_ip()
        assert result == "192.168.1.100"

    @patch("dosctl.lib.network.socket.socket")
    def test_returns_none_on_oserror(self, mock_socket_class):
        mock_socket = MagicMock()
        mock_socket.__enter__ = MagicMock(return_value=mock_socket)
        mock_socket.__exit__ = MagicMock(return_value=False)
        mock_socket.connect.side_effect = OSError("Network unreachable")
        mock_socket_class.return_value = mock_socket

        result = get_local_ip()
        assert result is None


# --- DOSBox launcher IPX integration tests ---


class TestDOSBoxIPXLaunch:
    """Test that the DOSBox launcher correctly injects IPX commands."""

    @patch("dosctl.lib.dosbox.subprocess.Popen")
    @patch("dosctl.lib.dosbox._ensure_ipx_conf")
    def test_launch_with_ipx_server(self, mock_ensure_conf, mock_popen, tmp_path):
        mock_ensure_conf.return_value = tmp_path / "ipx.conf"

        from dosctl.lib.dosbox import StandardDOSBoxLauncher
        from dosctl.lib.platform import get_platform

        platform = get_platform()
        launcher = StandardDOSBoxLauncher(platform)

        game_path = tmp_path / "game"
        game_path.mkdir()

        with patch.object(launcher, "get_executable", return_value="/usr/bin/dosbox"):
            ipx_config = IPXServerConfig(port=19900)
            launcher.launch_game(
                game_path=game_path,
                command="GAME.EXE",
                ipx=ipx_config,
            )

        cmd = mock_popen.call_args[0][0]
        assert "-conf" in cmd
        assert "IPXNET STARTSERVER 19900" in cmd
        # IPXNET command should come before GAME.EXE
        ipx_idx = cmd.index("IPXNET STARTSERVER 19900")
        game_idx = cmd.index("GAME.EXE")
        assert ipx_idx < game_idx
        # Should NOT have 'exit' command (net play stays open)
        assert "exit" not in cmd

    @patch("dosctl.lib.dosbox.subprocess.Popen")
    @patch("dosctl.lib.dosbox._ensure_ipx_conf")
    def test_launch_with_ipx_client(self, mock_ensure_conf, mock_popen, tmp_path):
        mock_ensure_conf.return_value = tmp_path / "ipx.conf"

        from dosctl.lib.dosbox import StandardDOSBoxLauncher
        from dosctl.lib.platform import get_platform

        platform = get_platform()
        launcher = StandardDOSBoxLauncher(platform)

        game_path = tmp_path / "game"
        game_path.mkdir()

        with patch.object(launcher, "get_executable", return_value="/usr/bin/dosbox"):
            ipx_config = IPXClientConfig(host="192.168.1.42", port=19900)
            launcher.launch_game(
                game_path=game_path,
                command="GAME.EXE",
                ipx=ipx_config,
            )

        cmd = mock_popen.call_args[0][0]
        assert "-conf" in cmd
        assert "IPXNET CONNECT 192.168.1.42 19900" in cmd

    @patch("dosctl.lib.dosbox.subprocess.Popen")
    def test_launch_without_ipx_unchanged(self, mock_popen, tmp_path):
        """Ensure normal launch (no IPX) is not affected."""
        from dosctl.lib.dosbox import StandardDOSBoxLauncher
        from dosctl.lib.platform import get_platform

        platform = get_platform()
        launcher = StandardDOSBoxLauncher(platform)

        game_path = tmp_path / "game"
        game_path.mkdir()

        with patch.object(launcher, "get_executable", return_value="/usr/bin/dosbox"):
            launcher.launch_game(
                game_path=game_path,
                command="GAME.EXE",
                exit_on_completion=True,
            )

        cmd = mock_popen.call_args[0][0]
        assert "-conf" not in cmd
        assert "IPXNET" not in " ".join(cmd)
        assert "exit" in cmd

    @patch("dosctl.lib.dosbox.subprocess.Popen")
    @patch("dosctl.lib.dosbox._ensure_ipx_conf")
    def test_ipx_suppresses_exit(self, mock_ensure_conf, mock_popen, tmp_path):
        """Even if exit_on_completion=True, IPX mode should suppress it."""
        mock_ensure_conf.return_value = tmp_path / "ipx.conf"

        from dosctl.lib.dosbox import StandardDOSBoxLauncher
        from dosctl.lib.platform import get_platform

        platform = get_platform()
        launcher = StandardDOSBoxLauncher(platform)

        game_path = tmp_path / "game"
        game_path.mkdir()

        with patch.object(launcher, "get_executable", return_value="/usr/bin/dosbox"):
            launcher.launch_game(
                game_path=game_path,
                command="GAME.EXE",
                ipx=IPXServerConfig(),
                exit_on_completion=True,
            )

        cmd = mock_popen.call_args[0][0]
        assert "exit" not in cmd


# --- IPX config file tests ---


class TestEnsureIPXConf:
    """Test the _ensure_ipx_conf helper."""

    def test_creates_config_file(self, tmp_path):
        from dosctl.lib.dosbox import _ensure_ipx_conf

        conf_path = tmp_path / "ipx.conf"
        with patch("dosctl.config.IPX_CONF_PATH", conf_path):
            result = _ensure_ipx_conf()

        assert conf_path.exists()
        assert result == conf_path
        content = conf_path.read_text()
        assert "[ipx]" in content
        assert "ipx=true" in content

    def test_does_not_overwrite_existing(self, tmp_path):
        """If ipx.conf already exists, it should not be overwritten."""
        from dosctl.lib.dosbox import _ensure_ipx_conf

        conf_path = tmp_path / "ipx.conf"
        conf_path.write_text("[ipx]\nipx=true\n# custom comment\n")

        with patch("dosctl.config.IPX_CONF_PATH", conf_path):
            result = _ensure_ipx_conf()

        content = conf_path.read_text()
        assert "# custom comment" in content


# --- Net command CLI tests ---


class TestNetHostCommand:
    """Test the 'dosctl net host' command."""

    @patch("dosctl.commands.net.is_dosbox_installed", return_value=False)
    @patch("dosctl.lib.decorators.create_collection")
    def test_host_no_dosbox(self, mock_collection, mock_dosbox):
        """Should show error when DOSBox is not installed."""
        runner = CliRunner()
        mock_collection.return_value.get_games.return_value = []

        result = runner.invoke(cli, ["net", "host", "abc12345"])
        assert "dosbox" in result.output.lower()

    @patch("dosctl.commands.net.get_local_ip", return_value="192.168.1.100")
    @patch("dosctl.commands.net.get_dosbox_launcher")
    @patch("dosctl.commands.net.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.net.install_game")
    @patch("dosctl.commands.net.executable_exists", return_value=True)
    @patch("dosctl.commands.net.get_or_prompt_command", return_value="GAME.EXE")
    @patch("dosctl.commands.net.set_game_command")
    @patch("dosctl.lib.decorators.create_collection")
    def test_host_success(
        self,
        mock_collection,
        mock_set_cmd,
        mock_get_cmd,
        mock_exe_exists,
        mock_install,
        mock_dosbox_installed,
        mock_launcher,
        mock_local_ip,
        tmp_path,
    ):
        """Should launch DOSBox with IPX server config."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        result = runner.invoke(cli, ["net", "host", "abc12345"])
        assert result.exit_code == 0
        assert "192.168.1.100" in result.output
        assert "IPX server" in result.output
        assert "dosctl net join abc12345 192.168.1.100" in result.output

        # Verify launcher was called with IPX config
        mock_launcher.return_value.launch_game.assert_called_once()
        call_kwargs = mock_launcher.return_value.launch_game.call_args[1]
        assert isinstance(call_kwargs["ipx"], IPXServerConfig)
        assert call_kwargs["ipx"].port == DEFAULT_IPX_PORT

    @patch("dosctl.commands.net.get_local_ip", return_value="192.168.1.100")
    @patch("dosctl.commands.net.get_dosbox_launcher")
    @patch("dosctl.commands.net.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.net.install_game")
    @patch("dosctl.commands.net.executable_exists", return_value=True)
    @patch("dosctl.commands.net.get_or_prompt_command", return_value="GAME.EXE")
    @patch("dosctl.commands.net.set_game_command")
    @patch("dosctl.lib.decorators.create_collection")
    def test_host_custom_port(
        self,
        mock_collection,
        mock_set_cmd,
        mock_get_cmd,
        mock_exe_exists,
        mock_install,
        mock_dosbox_installed,
        mock_launcher,
        mock_local_ip,
        tmp_path,
    ):
        """Should use custom port when --port is specified."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        result = runner.invoke(cli, ["net", "host", "abc12345", "--port", "9999"])
        assert result.exit_code == 0
        assert "9999" in result.output

        call_kwargs = mock_launcher.return_value.launch_game.call_args[1]
        assert call_kwargs["ipx"].port == 9999

    @patch("dosctl.commands.net.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.net.install_game")
    @patch("dosctl.lib.decorators.create_collection")
    def test_host_game_not_found(self, mock_collection, mock_install, mock_dosbox):
        """Should show error when game is not found."""
        runner = CliRunner()
        mock_install.side_effect = FileNotFoundError("Game not found")

        result = runner.invoke(cli, ["net", "host", "fake_id"])
        assert result.exit_code == 0
        assert "Game not found" in result.output


class TestNetJoinCommand:
    """Test the 'dosctl net join' command."""

    @patch("dosctl.commands.net.is_dosbox_installed", return_value=False)
    @patch("dosctl.lib.decorators.create_collection")
    def test_join_no_dosbox(self, mock_collection, mock_dosbox):
        """Should show error when DOSBox is not installed."""
        runner = CliRunner()
        result = runner.invoke(cli, ["net", "join", "abc12345", "192.168.1.42"])
        assert "dosbox" in result.output.lower()

    @patch("dosctl.commands.net.get_dosbox_launcher")
    @patch("dosctl.commands.net.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.net.install_game")
    @patch("dosctl.commands.net.executable_exists", return_value=True)
    @patch("dosctl.commands.net.get_or_prompt_command", return_value="GAME.EXE")
    @patch("dosctl.commands.net.set_game_command")
    @patch("dosctl.lib.decorators.create_collection")
    def test_join_success(
        self,
        mock_collection,
        mock_set_cmd,
        mock_get_cmd,
        mock_exe_exists,
        mock_install,
        mock_dosbox_installed,
        mock_launcher,
        tmp_path,
    ):
        """Should launch DOSBox with IPX client config."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        result = runner.invoke(cli, ["net", "join", "abc12345", "192.168.1.42"])
        assert result.exit_code == 0
        assert "192.168.1.42" in result.output

        call_kwargs = mock_launcher.return_value.launch_game.call_args[1]
        assert isinstance(call_kwargs["ipx"], IPXClientConfig)
        assert call_kwargs["ipx"].host == "192.168.1.42"
        assert call_kwargs["ipx"].port == DEFAULT_IPX_PORT

    @patch("dosctl.commands.net.get_dosbox_launcher")
    @patch("dosctl.commands.net.is_dosbox_installed", return_value=True)
    @patch("dosctl.commands.net.install_game")
    @patch("dosctl.commands.net.executable_exists", return_value=True)
    @patch("dosctl.commands.net.get_or_prompt_command", return_value="GAME.EXE")
    @patch("dosctl.commands.net.set_game_command")
    @patch("dosctl.lib.decorators.create_collection")
    def test_join_custom_port(
        self,
        mock_collection,
        mock_set_cmd,
        mock_get_cmd,
        mock_exe_exists,
        mock_install,
        mock_dosbox_installed,
        mock_launcher,
        tmp_path,
    ):
        """Should use custom port when --port is specified."""
        runner = CliRunner()
        game_path = tmp_path / "game"
        game_path.mkdir()
        mock_install.return_value = ({}, game_path)

        result = runner.invoke(
            cli, ["net", "join", "abc12345", "10.0.0.1", "--port", "9999"]
        )
        assert result.exit_code == 0

        call_kwargs = mock_launcher.return_value.launch_game.call_args[1]
        assert call_kwargs["ipx"].host == "10.0.0.1"
        assert call_kwargs["ipx"].port == 9999

    def test_join_missing_host_ip(self):
        """Should fail when host_ip argument is missing."""
        runner = CliRunner()
        result = runner.invoke(cli, ["net", "join", "abc12345"])
        assert result.exit_code != 0


class TestNetGroup:
    """Test the 'dosctl net' command group."""

    def test_net_shows_help(self):
        """Running 'dosctl net' without subcommand should show help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["net"])
        assert result.exit_code == 0
        assert "host" in result.output
        assert "join" in result.output

    def test_net_help_flag(self):
        """Running 'dosctl net --help' should show help."""
        runner = CliRunner()
        result = runner.invoke(cli, ["net", "--help"])
        assert result.exit_code == 0
        assert "Multiplayer" in result.output
