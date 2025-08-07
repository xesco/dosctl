# Collections Architecture

This directory contains the collection backend system for dosctl, which manages different sources of DOS games. The architecture uses a flexible class hierarchy that allows for easy extension to support new game collections.

## Class Hierarchy

```
BaseCollection (abstract)
├── ArchiveOrgCollection (intermediate base class)
    └── TotalDOSCollectionRelease14 (specific implementation)
    └── TotalDOSCollectionRelease15 (example of how to add new versions)
```

### BaseCollection

The abstract base class that defines the interface all collections must implement:

- `get_games()` - Returns list of available games
- `get_download_url(game_id)` - Gets download URL for a specific game
- `download_game(game_id, destination)` - Downloads a game to local storage

### ArchiveOrgCollection

An intermediate base class that provides common functionality for Archive.org-based collections:

- **Cache Management** - Downloads and caches game lists locally
- **Game Data Parsing** - Extracts game information from HTML listings
- **Download Handling** - Manages HTTP downloads with progress bars
- **ZIP Extraction** - Handles unzipping games to installation directories

Key features:
- Automatic cache directory creation
- HTTP request handling with proper headers
- Game ID generation using SHA1 hashes
- Filename parsing to extract game names and years
- Progress bars for downloads using tqdm

### Specific Implementations

Each specific collection version (like `TotalDOSCollectionRelease14`) extends `ArchiveOrgCollection` and provides:

- **Collection Name** - Human-readable name for the collection
- **Download URL Pattern** - How to construct download URLs for this specific collection
- **Custom Parsing** (optional) - Override filename parsing if the collection has different patterns

## Adding a New Collection

To add support for a new collection version, follow these steps:

### 1. Create the Collection Class

See the example in `archive_org.py` for `TotalDOSCollectionRelease15`:

```python
class TotalDOSCollectionRelease15(ArchiveOrgCollection):
    """
    Specific implementation for Total DOS Collection Release 15.
    """

    def __init__(self, source: str, cache_dir: str):
        super().__init__(source, cache_dir, "Total DOS Collection Release 15")

    def _build_download_url(self, encoded_full_path: str) -> str:
        """
        Builds the download URL specific to TDC Release 15 structure.
        """
        return f"https://archive.org/download/{self.item_name}/TDC_Release_15.zip/{encoded_full_path}"

    def _parse_filename(self, filename: str) -> Dict:
        """
        Override if Release 15 has different filename patterns.
        """
        # Custom parsing logic for Release 15 if needed
        return super()._parse_filename(filename)
```

### 2. Register in Factory

Add your new collection to `factory.py`:

```python
COLLECTION_TYPES = {
    "tdc_release_14": TotalDOSCollectionRelease14,
    "tdc_release_15": TotalDOSCollectionRelease15,  # Add this line
}
```

### 3. Update Configuration

Update the main configuration to include the new collection source URL and make it available as a command-line option.

## Key Extension Points

When creating a new collection, you can override these methods:

### Required Override
- `_build_download_url(encoded_full_path)` - Must implement URL construction for your collection

### Optional Overrides
- `_parse_filename(filename)` - Override if your collection has different filename patterns
- `ensure_cache_is_present()` - Override if your collection uses a different caching mechanism
- `_populate_games_data()` - Override if your collection has a different data format

## File Structure

```
collections/
├── README.md              # This file - architecture documentation
├── __init__.py           # Package initialization
├── base.py               # BaseCollection abstract class
├── archive_org.py        # ArchiveOrgCollection and specific implementations
└── factory.py            # Factory pattern for creating collections
```

## Usage Example

```python
from dosctl.collections.factory import create_collection

# Create a collection instance
collection = create_collection(
    "tdc_release_14",
    "https://ia800906.us.archive.org/view_archive.php?archive=/4/items/Total_DOS_Collection_Release_14/TDC_Release_14.zip",
    "/path/to/cache"
)

# Load game data
collection.load()

# Get all games
games = collection.get_games()

# Download a specific game
collection.download_game("abc12345", "/path/to/downloads")
```

## Benefits of This Architecture

1. **Extensibility** - Easy to add new collection versions without modifying existing code
2. **Code Reuse** - Common Archive.org functionality is shared across implementations
3. **Testability** - Each layer can be tested independently
4. **Maintainability** - Changes to specific collections don't affect others
5. **Factory Pattern** - Centralized creation logic makes it easy to switch between collections

This design allows dosctl to support multiple game collections while keeping the codebase clean and maintainable.
