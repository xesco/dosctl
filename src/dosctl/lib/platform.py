"""Platform abstraction layer for cross-platform compatibility."""

import shutil
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional


class PlatformBase(ABC):
    """Abstract base class for platform-specific operations."""

    @abstractmethod
    def get_config_dir(self) -> Path:
        """Get platform-specific configuration directory."""
        pass

    @abstractmethod
    def get_data_dir(self) -> Path:
        """Get platform-specific data directory."""
        pass

    @abstractmethod
    def get_dosbox_executable(self) -> Optional[str]:
        """Find DOSBox executable for this platform."""
        pass

    @abstractmethod
    def format_dosbox_mount_command(self, drive: str, path: Path) -> str:
        """Format mount command for platform-specific DOSBox."""
        pass

    @abstractmethod
    def get_executable_extensions(self) -> List[str]:
        """Get valid executable extensions for this platform."""
        pass

    def get_downloads_dir(self) -> Path:
        """Get downloads directory."""
        return self.get_data_dir() / "downloads"

    def get_installed_dir(self) -> Path:
        """Get installed games directory."""
        return self.get_data_dir() / "installed"

    def get_collections_cache_dir(self) -> Path:
        """Get collections cache directory."""
        return self.get_data_dir() / "collections"


class UnixPlatform(PlatformBase):
    """Platform implementation for Unix/Linux systems."""

    def get_config_dir(self) -> Path:
        """Get Unix-style configuration directory."""
        return Path.home() / ".config" / "dosctl"

    def get_data_dir(self) -> Path:
        """Get Unix-style data directory."""
        return Path.home() / ".local" / "share" / "dosctl"

    def get_dosbox_executable(self) -> Optional[str]:
        """Find DOSBox executable on Unix systems."""
        # Check for dosbox-staging first (preferred), then standard dosbox
        candidates = ['dosbox-staging', 'dosbox']
        for candidate in candidates:
            if shutil.which(candidate):
                return candidate
        return None

    def format_dosbox_mount_command(self, drive: str, path: Path) -> str:
        """Format mount command for Unix DOSBox."""
        return f'MOUNT {drive} "{path}"'

    def get_executable_extensions(self) -> List[str]:
        """Get DOS executable extensions."""
        return ['exe', 'com', 'bat']


class MacOSPlatform(UnixPlatform):
    """Platform implementation for macOS."""

    def get_config_dir(self) -> Path:
        """Get the configuration directory for macOS."""
        return Path.home() / ".local" / "share" / "dosctl"

    def get_data_dir(self) -> Path:
        """Get the data directory for macOS."""
        return Path.home() / ".local" / "share" / "dosctl"


class WindowsPlatform(PlatformBase):
    """Platform implementation for Windows systems."""

    def get_config_dir(self) -> Path:
        """Get Windows-style configuration directory."""
        return Path.home() / "AppData" / "Local" / "dosctl"

    def get_data_dir(self) -> Path:
        """Get Windows-style data directory."""
        return Path.home() / "AppData" / "Local" / "dosctl"

    def get_dosbox_executable(self) -> Optional[str]:
        """Find DOSBox executable on Windows systems."""
        # Check if DOSBox is in PATH
        if shutil.which('dosbox.exe'):
            return 'dosbox.exe'
        if shutil.which('dosbox'):
            return 'dosbox'

        # Check common installation paths
        common_paths = [
            Path("C:/Program Files/DOSBox"),
            Path("C:/Program Files (x86)/DOSBox"),
        ]

        for base_path in common_paths:
            if base_path.exists():
                exe_path = base_path / "dosbox.exe"
                if exe_path.exists():
                    return str(exe_path)

        return None

    def format_dosbox_mount_command(self, drive: str, path: Path) -> str:
        """Format mount command for Windows DOSBox."""
        # Convert to forward slashes (DOSBox accepts these even on Windows)
        # and ensure proper quoting for paths with spaces
        path_str = str(path).replace('\\', '/')
        return f'MOUNT {drive} "{path_str}"'

    def get_executable_extensions(self) -> List[str]:
        """Get DOS executable extensions for Windows."""
        return ['exe', 'com', 'bat']


class PlatformFactory:
    """Factory for creating platform-specific implementations."""

    @staticmethod
    def create_platform() -> PlatformBase:
        """Create the appropriate platform implementation based on the current system."""
        if sys.platform.startswith('win'):
            return WindowsPlatform()
        elif sys.platform == 'darwin':
            return MacOSPlatform()
        else:
            # Default to Unix for Linux and other Unix-like systems
            return UnixPlatform()


# Singleton instance for the current platform
_platform_instance: Optional[PlatformBase] = None


def get_platform() -> PlatformBase:
    """Get the current platform instance (singleton)."""
    global _platform_instance
    if _platform_instance is None:
        _platform_instance = PlatformFactory.create_platform()
    return _platform_instance
