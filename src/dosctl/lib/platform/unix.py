"""Unix/Linux platform implementation."""

import shutil
from pathlib import Path
from typing import List, Optional

from .base import PlatformBase


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
