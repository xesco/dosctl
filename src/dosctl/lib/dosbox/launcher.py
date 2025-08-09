"""DOSBox launcher factory and utilities."""

import shutil
from typing import Optional

from .base import DOSBoxLauncher
from .standard import StandardDOSBoxLauncher
from ..platform import get_platform


def create_dosbox_launcher() -> Optional[DOSBoxLauncher]:
    """Create the best available DOSBox launcher for the current platform."""
    platform = get_platform()

    # For now, we only have the standard launcher
    # In the future, we can add DOSBox-Staging, DOSBox-X, etc.
    launcher = StandardDOSBoxLauncher(platform)

    if launcher.is_available():
        return launcher

    return None


# Singleton instance
_launcher_instance: Optional[DOSBoxLauncher] = None


def get_dosbox_launcher() -> DOSBoxLauncher:
    """Get the DOSBox launcher instance (singleton)."""
    global _launcher_instance
    if _launcher_instance is None:
        _launcher_instance = create_dosbox_launcher()
        if _launcher_instance is None:
            raise RuntimeError("No DOSBox installation found")
    return _launcher_instance


def is_dosbox_available() -> bool:
    """Check if DOSBox is available (backward compatibility)."""
    try:
        launcher = create_dosbox_launcher()
        return launcher is not None
    except Exception:
        return False


def reset_launcher():
    """Reset the launcher instance (useful for testing)."""
    global _launcher_instance
    _launcher_instance = None
