"""Abstract base class for platform-specific operations."""

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

    def get_cache_dir(self) -> Path:
        """Get platform-specific cache directory. Default implementation."""
        return self.get_data_dir() / "cache"

    def get_downloads_dir(self) -> Path:
        """Get downloads directory."""
        return self.get_data_dir() / "downloads"

    def get_installed_dir(self) -> Path:
        """Get installed games directory."""
        return self.get_data_dir() / "installed"

    def get_collections_cache_dir(self) -> Path:
        """Get collections cache directory."""
        return self.get_data_dir() / "collections"
