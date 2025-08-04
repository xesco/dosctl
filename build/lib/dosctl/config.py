from pathlib import Path

# Define the base directories for config and data
# On macOS, this will resolve to /Users/<user>/.config/dosctl
CONFIG_DIR = Path.home() / ".config" / "dosctl"
# On macOS, this will resolve to /Users/<user>/.local/share/dosctl
DATA_DIR = Path.home() / ".local" / "share" / "dosctl"

# Define the specific cache directory for collections
COLLECTION_CACHE_DIR = DATA_DIR / "collections"

# Define the default source URL for the main game collection
DEFAULT_COLLECTION_SOURCE = "https://ia802302.us.archive.org/34/items/Total_DOS_Collection_Release_13/TotalDOSCollection-Release13.txt"

def ensure_dirs_exist():
    """Create the config and data directories if they don't exist."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    COLLECTION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
