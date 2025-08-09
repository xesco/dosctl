"""Platform factory for creating platform-specific implementations."""

import sys
from typing import Optional

from .base import PlatformBase
from .unix import UnixPlatform, MacOSPlatform
from .windows import WindowsPlatform


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


def reset_platform():
    """Reset the platform instance (useful for testing)."""
    global _platform_instance
    _platform_instance = None
