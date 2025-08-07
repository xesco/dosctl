from pathlib import Path

# Define the base directories for config and data
CONFIG_DIR = Path.home() / ".config" / "dosctl"
DATA_DIR = Path.home() / ".local" / "share" / "dosctl"

# Define the specific cache directory for collections
COLLECTION_CACHE_DIR = DATA_DIR / "collections"

# Define game-specific directories
DOWNLOADS_DIR = DATA_DIR / "downloads"
INSTALLED_DIR = DATA_DIR / "installed"

# Define the default source URL for the main game collection
DEFAULT_COLLECTION_SOURCE = "https://ia800906.us.archive.org/view_archive.php?archive=/4/items/Total_DOS_Collection_Release_14/TDC_Release_14.zip"

def ensure_dirs_exist():
    """Create the config and data directories if they don't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COLLECTION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
    INSTALLED_DIR.mkdir(parents=True, exist_ok=True)
