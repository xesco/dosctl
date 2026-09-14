# Collections

A collection is a web page that lists one zip archive per game. dosctl downloads games from that page. This package holds the code that reads such a list, keeps it in a local catalog file, and downloads and unpacks an archive when a game is played. This page is for a developer who wants to understand that code or add a second collection. It explains how dosctl uses a collection, describes each class and the catalog file, and then gives the steps to add a collection.

## How dosctl uses a collection

`ensure_cache` (`src/dosctl/lib/decorators.py`) wraps every command that needs the catalog. The wrapper creates the collection with `create_collection` (`factory.py`), calls `ensure_cache_is_present` on it and passes it to the command. The type it asks for is `tdc_release_14`, and the source URL and the cache directory come from `DEFAULT_COLLECTION_SOURCE` and `COLLECTION_CACHE_DIR` in `src/dosctl/config.py`. No flag selects a collection.

A collection does four things in turn.

1. It downloads the source page and writes a line per zip archive to the catalog file `games.txt` in the cache directory (see [The catalog file](#the-catalog-file)).
2. It reads that file into memory when a command asks for games.
3. It downloads a game's archive into the downloads directory.
4. It unpacks the archive into the game's install directory.

## The classes

Three classes form a chain. `BaseCollection` declares the interface. `ArchiveOrgCollection` implements it for a page on the Internet Archive. `TotalDOSCollectionRelease14` fills in the one detail that differs between collections on that site.

```
BaseCollection
└── ArchiveOrgCollection
    └── TotalDOSCollectionRelease14
```

### BaseCollection

`BaseCollection` (`base.py`) is an abstract class. It stores the URL of the list in the attribute `source` and declares three abstract methods.

| Method | What it does |
|--------|--------------|
| `load()` | Makes the games available |
| `get_games()` | Returns the games as a list of dicts |
| `download_game(game_name, destination)` | Downloads one game into the directory `destination` |

### ArchiveOrgCollection

`ArchiveOrgCollection` (`archive_org.py`) implements `BaseCollection` for an Internet Archive page that lists zip archives. Its constructor takes `source`, `cache_dir` and `collection_name`, creates the cache directory when it does not exist, and reads the item name (the second-to-last part of the source URL split on `/`), which `_build_download_url` uses. The table lists its public methods.

| Method | What it does |
|--------|--------------|
| `ensure_cache_is_present(force_refresh=False)` | Downloads the source page and writes `games.txt` when the file is missing or `force_refresh` is true; prints `Downloading game list from <source>...` and `✅ Game list refreshed successfully.` |
| `load(force_refresh=False)` | Calls `ensure_cache_is_present`, then reads `games.txt` into memory |
| `get_games()` | Returns every game as a dict with the keys `id`, `name`, `year` and `full_path`; reads `games.txt` first when nothing is loaded |
| `find_game(game_id)` | Returns the game with that ID, or `None` |
| `get_download_url(game_id)` | Returns the archive URL for the game, or `None` when the ID is unknown |
| `download_game(game_id, destination, force=False)` | Downloads the archive to `<destination>/<name>.zip` with a progress bar and returns that path; returns the path without downloading when the file exists and `force` is false; returns `None` after printing an error when the download fails or stops short of the size the server announced |
| `unzip_game(game_id, download_path, install_path)` | Unpacks `<download_path>/<name>.zip` into `install_path` |

`unzip_game` refuses an archive whose member paths are absolute, start with a drive letter or contain `..`, so an archive cannot write outside the install directory. It unpacks into a temporary directory next to `install_path` and renames that directory into place when every member has been written, so a failed unpack leaves no half-filled install directory.

Three methods are meant to be overridden. `_build_download_url(encoded_full_path)` turns the URL-encoded archive path into the download URL; the base class raises `NotImplementedError`, so every subclass must define it. `_parse_filename(filename)` takes an archive's file name and returns a dict with `name` (the file name without `.zip`) and `year` (the first four digits in parentheses, or `None`). `_populate_games_data()` reads `games.txt` into memory and skips blank lines and lines without exactly four fields.

### TotalDOSCollectionRelease14

`TotalDOSCollectionRelease14` (`archive_org.py`) is the one collection dosctl ships. It passes the name `Total DOS Collection Release 14` to the constructor and defines `_build_download_url` as `https://archive.org/download/<item name>/TDC_Release_14.zip/<encoded path>` (the code is in step 1 of [Adding a collection](#adding-a-collection)).

## The catalog file

`ensure_cache_is_present` finds every `href` ending in `.zip` on the source page and writes one line per archive to `games.txt`, with four fields separated by tabs. The table gives each field and where it comes from.

| Field | Comes from |
|-------|------------|
| ID | The first 8 characters of the SHA-1 hash of the decoded archive path |
| Name | The `name` that `_parse_filename` returns |
| Year | The `year` that `_parse_filename` returns, written empty when it is `None` |
| Archive path | The last part of the `href`, URL-decoded |

```
4e771c98	2112 (19xx)(Anonymous) [Adventure, Interactive Fiction]		TDC release 14/19xx/2112 (19xx)(Anonymous) [Adventure, Interactive Fiction].zip
```

## Adding a collection

Adding a collection from an Internet Archive page that lists zip archives takes four steps.

1. Add a subclass of `ArchiveOrgCollection` to `archive_org.py` that passes the collection's name to the constructor and defines `_build_download_url`. `TotalDOSCollectionRelease14` is the model:

    ```python
    class TotalDOSCollectionRelease14(ArchiveOrgCollection):
        def __init__(self, source: str, cache_dir: str):
            super().__init__(source, cache_dir, "Total DOS Collection Release 14")

        def _build_download_url(self, encoded_full_path: str) -> str:
            return f"https://archive.org/download/{self.item_name}/TDC_Release_14.zip/{encoded_full_path}"
    ```

    Override `_parse_filename` too (described under [ArchiveOrgCollection](#archiveorgcollection)) when you need to parse the file name differently.

2. Register the class under a new key in `COLLECTION_REGISTRY` in `factory.py`. `create_collection` raises `ValueError` for a key that is not there, and `get_available_collections` returns the keys.

3. Make dosctl use the new key by changing the type passed to `create_collection` in `ensure_cache` (`src/dosctl/lib/decorators.py`) and setting `DEFAULT_COLLECTION_SOURCE` in `src/dosctl/config.py` to the new page.

4. Run the tests of this package with `uv run pytest tests/test_collections.py`.

## Files

| File | Holds |
|------|-------|
| `base.py` | `BaseCollection` |
| `archive_org.py` | `ArchiveOrgCollection` and `TotalDOSCollectionRelease14` |
| `factory.py` | `COLLECTION_REGISTRY`, `create_collection` and `get_available_collections` |
| `__init__.py` | Nothing; it marks the package |

The user-facing side of the same flow (the `list`, `search`, `play` and `refresh` commands, and where the catalog and the games are stored) is in the main [README](../../../README.md).
