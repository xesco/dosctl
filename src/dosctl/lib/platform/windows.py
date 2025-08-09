"""Windows platform implementation."""

import shutil
from pathlib import Path
from typing import List, Optional

from .base import PlatformBase


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
