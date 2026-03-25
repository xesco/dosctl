"""Tests for lib/platform.py."""
import sys
from pathlib import Path
from unittest.mock import patch

from dosctl.lib.platform import (
    UnixPlatform,
    MacOSPlatform,
    WindowsPlatform,
    PlatformFactory,
    get_platform,
)


class TestUnixPlatform:
    def setup_method(self):
        self.platform = UnixPlatform()

    def test_config_dir(self):
        assert self.platform.get_config_dir() == Path.home() / ".config" / "dosctl"

    def test_data_dir(self):
        assert self.platform.get_data_dir() == Path.home() / ".local" / "share" / "dosctl"

    def test_format_mount_command(self):
        assert self.platform.format_dosbox_mount_command("C", Path("/home/user/game")) == \
            'MOUNT C "/home/user/game"'

    def test_get_dosbox_executable_found(self):
        with patch("shutil.which", return_value="/usr/bin/dosbox-staging"):
            assert self.platform.get_dosbox_executable() == "dosbox-staging"

    def test_get_dosbox_executable_not_found(self):
        with patch("shutil.which", return_value=None):
            assert self.platform.get_dosbox_executable() is None


class TestMacOSPlatform:
    def test_config_and_data_dirs_are_same(self):
        p = MacOSPlatform()
        assert p.get_config_dir() == p.get_data_dir()


class TestWindowsPlatform:
    def setup_method(self):
        self.platform = WindowsPlatform()

    def test_data_dir(self):
        assert self.platform.get_data_dir() == Path.home() / "AppData" / "Local" / "dosctl"

    def test_format_mount_command_converts_backslashes(self):
        result = self.platform.format_dosbox_mount_command("C", Path("C:\\Users\\user\\game"))
        assert "\\" not in result.split('"')[1]

    def test_get_dosbox_executable_in_path(self):
        with patch("shutil.which", return_value="dosbox.exe"):
            assert self.platform.get_dosbox_executable() == "dosbox.exe"


class TestPlatformFactory:
    def test_creates_macos_on_darwin(self):
        with patch.object(sys, "platform", "darwin"):
            assert isinstance(PlatformFactory.create_platform(), MacOSPlatform)

    def test_creates_windows_on_win32(self):
        with patch.object(sys, "platform", "win32"):
            assert isinstance(PlatformFactory.create_platform(), WindowsPlatform)

    def test_creates_unix_on_linux(self):
        with patch.object(sys, "platform", "linux"):
            assert isinstance(PlatformFactory.create_platform(), UnixPlatform)


class TestGetPlatformSingleton:
    def test_returns_same_instance(self):
        import dosctl.lib.platform as platform_module
        platform_module._platform_instance = None
        assert get_platform() is get_platform()
        platform_module._platform_instance = None
