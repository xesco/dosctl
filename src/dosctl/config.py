import click

from .lib.platform import get_platform

# Get platform-specific directories
_platform = get_platform()

# Define the base directories for config and data (platform-aware)
CONFIG_DIR = _platform.get_config_dir()
DATA_DIR = _platform.get_data_dir()

# Define the specific cache directory for collections
COLLECTION_CACHE_DIR = _platform.get_collections_cache_dir()

# Define game-specific directories
DOWNLOADS_DIR = _platform.get_downloads_dir()
INSTALLED_DIR = _platform.get_installed_dir()

# IPX networking config file path
IPX_CONF_PATH = CONFIG_DIR / "ipx.conf"

# Default source URL for the main game collection
DEFAULT_COLLECTION_SOURCE = "https://ia800906.us.archive.org/view_archive.php?archive=/4/items/Total_DOS_Collection_Release_14/TDC_Release_14.zip"


def ensure_dirs_exist():
    """Create the config and data directories if they don't exist."""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        COLLECTION_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        DOWNLOADS_DIR.mkdir(parents=True, exist_ok=True)
        INSTALLED_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError as e:
        click.echo(f"Warning: Could not create directories: {e}", err=True)
