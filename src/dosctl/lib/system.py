import shutil

def is_dosbox_installed() -> bool:
    """Checks if the 'dosbox' command is available in the system's PATH."""
    return shutil.which('dosbox') is not None
