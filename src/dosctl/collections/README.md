# Collections

A collection is a list of zip archives, one per game, that dosctl reads games from: a web page on the Internet Archive, or a directory on the machine. This package holds the code that reads such a list, looks games up by ID, fetches a game's archive and unpacks it when the game is played. This page is for a developer who wants to understand that code or add a collection. It explains how dosctl chooses and uses a collection, describes each class and the catalog file, and then gives the steps to add a collection.

## How dosctl uses a collection

`ensure_cache` (`src/dosctl/lib/decorators.py`) wraps every command that needs the list of games. The wrapper creates the collection with `create_collection` (`factory.py`), calls `ensure_cache_is_present` on it and passes it to the command. The type key, the source and the cache directory come from `DEFAULT_COLLECTION_TYPE`, `DEFAULT_COLLECTION_SOURCE` and `COLLECTION_CACHE_DIR` in `src/dosctl/config.py`. The table gives the two environment variables that set the type key and the source, and their defaults.

| Variable | Sets | Default |
|----------|------|---------|
| `DOSCTL_COLLECTION` | The type key, one of the keys of `COLLECTION_REGISTRY` in `factory.py` | `tdc_release_14` |
| `DOSCTL_COLLECTION_SOURCE` | The source: the URL of the list for `tdc_release_14`, the directory for `local_file` | The URL of Total DOS Collection Release 14 |

A collection does four things in turn.

1. It builds the list of games from the source.
2. It gives a command the games as a list of dicts, or one game by ID.
3. It fetches a game's archive.
4. It unpacks the archive into the game's install directory.

## The classes

Four classes form a tree. `BaseCollection` declares the interface. `CatalogCollection` implements the parts every collection shares: the list of games in memory, the lookup by ID and the unpacking. `ArchiveOrgCollection` reads the list from a page on the Internet Archive and downloads archives. `TotalDOSCollectionRelease14` fills in the one detail that differs between collections on that site. `LocalFileCollection` reads the list from a directory.

```
BaseCollection
└── CatalogCollection
    ├── ArchiveOrgCollection
    │   └── TotalDOSCollectionRelease14
    └── LocalFileCollection
```

### BaseCollection

`BaseCollection` (`base.py`) is an abstract class. It stores the source in the attribute `source` and declares three abstract methods.

| Method | What it does |
|--------|--------------|
| `load()` | Makes the games available |
| `get_games()` | Returns the games as a list of dicts |
| `download_game(game_name, destination)` | Fetches one game into the directory `destination` |

### CatalogCollection

`CatalogCollection` (`base.py`) implements `BaseCollection` for a collection whose games are zip archives and whose list of games is held in memory. Its constructor takes `source`, `cache_dir` and `collection_name`. It creates the cache directory when it does not exist. Two methods are abstract: `ensure_cache_is_present(force_refresh=False)` makes the list available, and `_populate_games_data()` fills the list in memory. The table lists the methods every subclass gets.

| Method | What it does |
|--------|--------------|
| `load(force_refresh=False)` | Calls `ensure_cache_is_present`, then `_populate_games_data` |
| `get_games()` | Returns every game as a dict with the keys `id`, `name`, `year` and `full_path`; calls `_populate_games_data` first when the list is empty |
| `find_game(game_id)` | Returns the game with that ID, or `None` |
| `unzip_game(game_id, download_path, install_path)` | Unpacks `<download_path>/<name>.zip` into `install_path`; raises `FileNotFoundError` when the ID is unknown or the file is missing |

`_parse_filename(filename)` takes an archive's file name and returns a dict with `name` (the file name without its `.zip` extension, in any case) and `year` (the first four digits in parentheses, or `None`). A subclass overrides it when it needs to parse the file name differently.

`unzip_game` refuses an archive whose member paths are absolute, start with a drive letter or contain `..`, so an archive cannot write outside the install directory. It unpacks into a temporary directory next to `install_path` and renames that directory into place when every member has been written, so a failed unpack leaves no half-filled install directory. When a member uses a compression method that Python's `zipfile` cannot read (PKZIP Implode, common in archives from the early 1990s), it runs the `unzip` command on the archive instead, after the same path check, and raises `RuntimeError` when `unzip` is not installed. The check, the temporary directory and the fallback are in `_unpack_archive(zip_filepath, install_path)`, which a subclass calls to unpack an archive from another place.

### ArchiveOrgCollection

`ArchiveOrgCollection` (`archive_org.py`) extends `CatalogCollection` for an Internet Archive page that lists zip archives. Its constructor reads the item name (the second-to-last part of the source URL split on `/`), which `_build_download_url` uses. It writes the list of games to the catalog file `games.txt` in the cache directory (see [The catalog file](#the-catalog-file)). It reads that file back. The table lists the methods it adds or defines.

| Method | What it does |
|--------|--------------|
| `ensure_cache_is_present(force_refresh=False)` | Downloads the source page and writes `games.txt` when the file is missing or `force_refresh` is true; prints `Downloading game list from <source>...` and `✅ Game list refreshed successfully.` |
| `_populate_games_data()` | Reads `games.txt` into memory and skips blank lines and lines without exactly four fields |
| `get_download_url(game_id)` | Returns the archive URL for the game, or `None` when the ID is unknown |
| `download_game(game_id, destination, force=False)` | Downloads the archive to `<destination>/<name>.zip` with a progress bar and returns that path; returns the path without downloading when the file exists and `force` is false; returns `None` after printing an error when the download fails or stops short of the size the server announced |

`_build_download_url(encoded_full_path)` turns the URL-encoded archive path into the download URL. The base class raises `NotImplementedError`, so every subclass must define it.

### TotalDOSCollectionRelease14

`TotalDOSCollectionRelease14` (`archive_org.py`) is the collection dosctl uses by default. It passes the name `Total DOS Collection Release 14` to the constructor. It defines `_build_download_url` as `https://archive.org/download/<item name>/TDC_Release_14.zip/<encoded path>` (the code is in step 1 of [Adding a collection on the Internet Archive](#adding-a-collection-on-the-internet-archive)).

### LocalFileCollection

`LocalFileCollection` (`local_file.py`) extends `CatalogCollection` for zip archives in a directory on the machine. The source is the directory's path. A leading `~` stands for the home directory. The collection scans the directory on every run and writes no catalog file, so an archive added to or removed from the directory shows up on the next command. The table lists the methods it defines.

| Method | What it does |
|--------|--------------|
| `ensure_cache_is_present(force_refresh=False)` | Scans the directory; prints `✅ Found <count> games in '<directory>'.` when `force_refresh` is true; raises `click.ClickException` with `Collection directory not found: '<directory>'` when the directory does not exist |
| `_populate_games_data()` | Scans the directory into memory |
| `get_archive_path(game_id)` | Returns the archive's path in the directory, or `None` when the ID is unknown |
| `download_game(game_id, destination, force=False)` | Returns the archive's path in the directory and copies nothing to `destination`; returns `None` after printing an error when the archive has gone since the scan; raises `FileNotFoundError` when the ID is unknown |
| `unzip_game(game_id, download_path, install_path)` | Unpacks the archive from the directory into `install_path` and ignores `download_path`; raises `FileNotFoundError` when the ID is unknown or the archive has gone |

A scan takes every file in the directory and its subdirectories whose extension is `.zip` in any case, sorted by path. The table gives each field of a game and where it comes from.

| Field | Comes from |
|-------|------------|
| `id` | The first 8 characters of the SHA-1 hash of the archive's path relative to the directory, with `/` between parts |
| `name` | The `name` that `_parse_filename` returns |
| `year` | The `year` that `_parse_filename` returns |
| `full_path` | The archive's path relative to the directory, with `/` between parts |

Because the archive is never copied into the downloads directory, `dosctl info` never reports a game of this collection as downloaded, and `dosctl delete` never removes a file from the directory.

## The catalog file

`ArchiveOrgCollection.ensure_cache_is_present` finds every `href` ending in `.zip` on the source page and writes one line per archive to `games.txt`, with four fields separated by tabs. The table gives each field and where it comes from.

| Field | Comes from |
|-------|------------|
| ID | The first 8 characters of the SHA-1 hash of the decoded archive path |
| Name | The `name` that `_parse_filename` returns |
| Year | The `year` that `_parse_filename` returns, written empty when it is `None` |
| Archive path | The last part of the `href`, URL-decoded |

```
4e771c98	2112 (19xx)(Anonymous) [Adventure, Interactive Fiction]		TDC release 14/19xx/2112 (19xx)(Anonymous) [Adventure, Interactive Fiction].zip
```

## Adding a collection on the Internet Archive

Adding a collection from an Internet Archive page that lists zip archives takes four steps.

1. Add a subclass of `ArchiveOrgCollection` to `archive_org.py` that passes the collection's name to the constructor and defines `_build_download_url`. `TotalDOSCollectionRelease14` is the model:

    ```python
    class TotalDOSCollectionRelease14(ArchiveOrgCollection):
        def __init__(self, source: str, cache_dir: str):
            super().__init__(source, cache_dir, "Total DOS Collection Release 14")

        def _build_download_url(self, encoded_full_path: str) -> str:
            return f"https://archive.org/download/{self.item_name}/TDC_Release_14.zip/{encoded_full_path}"
    ```

    Override `_parse_filename` too (described under [CatalogCollection](#catalogcollection)) when you need to parse the file name differently.

2. Register the class under a new key in `COLLECTION_REGISTRY` in `factory.py`. `create_collection` raises `ValueError` for a key that is not there, and `get_available_collections` returns the keys.

3. Select the collection by setting `DOSCTL_COLLECTION` to the new key and `DOSCTL_COLLECTION_SOURCE` to the page's URL (see [How dosctl uses a collection](#how-dosctl-uses-a-collection)), or make it the default by changing `DEFAULT_COLLECTION_TYPE` and `TDC_RELEASE_14_SOURCE` in `src/dosctl/config.py`.

4. Run the tests of this package with `uv run pytest tests/test_collections.py tests/test_local_file.py`.

## Adding a collection of another kind

A collection that is neither an Internet Archive page nor a directory extends `CatalogCollection` directly. The subclass defines `ensure_cache_is_present` and `_populate_games_data` to build the list of games, `download_game` to fetch an archive, and `unzip_game` when the archive is not at `<download_path>/<name>.zip`. `LocalFileCollection` is the model. Then steps 2 to 4 of [Adding a collection on the Internet Archive](#adding-a-collection-on-the-internet-archive) apply.

## Files

| File | Holds |
|------|-------|
| `base.py` | `BaseCollection` and `CatalogCollection` |
| `archive_org.py` | `ArchiveOrgCollection` and `TotalDOSCollectionRelease14` |
| `local_file.py` | `LocalFileCollection` |
| `factory.py` | `COLLECTION_REGISTRY`, `create_collection` and `get_available_collections` |
| `__init__.py` | Nothing; it marks the package |

The user-facing side of the same flow (the `list`, `search`, `play` and `refresh` commands, how to point dosctl at a directory, and where the catalog and the games are stored) is in the main [README](../../../README.md).
