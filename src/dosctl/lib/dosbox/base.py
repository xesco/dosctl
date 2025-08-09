"""Abstract base class for DOSBox launchers."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any

from ..platform.base import PlatformBase


class DOSBoxLauncher(ABC):
    """Abstract base class for DOSBox launchers."""

    def __init__(self, platform: PlatformBase):
        self.platform = platform

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this DOSBox variant is available on the system."""
        pass

    @abstractmethod
    def launch_game(self, game_path: Path, command: str, **options) -> None:
        """Launch a game with DOSBox."""
        pass

    def get_executable(self) -> str:
        """Get the DOSBox executable path."""
        executable = self.platform.get_dosbox_executable()
        if not executable:
            raise RuntimeError("DOSBox executable not found")
        return executable
