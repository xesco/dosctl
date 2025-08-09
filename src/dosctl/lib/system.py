import shutil
from .dosbox.launcher import is_dosbox_available

def is_dosbox_installed() -> bool:
    """Checks if DOSBox is available on the system (backward compatibility)."""
    return is_dosbox_available()
