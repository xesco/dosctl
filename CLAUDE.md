# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

dosctl is a Python CLI tool for managing and playing DOS games via DOSBox. It downloads games from Archive.org collections (currently Total DOS Collection Release 14), manages installations, and launches them through DOSBox. Supports Linux, macOS, and Windows.

## Development Commands

```bash
# Install in dev mode (creates 'dosctl' CLI entry point)
pip install -e ".[dev]"

# Run all tests
python -m pytest

# Run a single test file
python -m pytest tests/test_config.py

# Run a specific test
python -m pytest tests/test_config.py::test_function_name

# Build package
python -m build
```

## Architecture

### CLI Layer (Click framework)
- **Entry point:** `src/dosctl/main.py` — defines the `cli` Click group with subcommands: list, search, play, inspect, delete, refresh, net
- **Commands:** `src/dosctl/commands/` — each file is one subcommand (net.py is a Click subgroup with host/join)

### Core Pattern: `@ensure_cache` decorator (`src/dosctl/lib/decorators.py`)
Most commands are wrapped with `@ensure_cache`, which automatically creates directories, initializes the game collection, and loads/downloads the game cache before passing the collection to the command handler. This is the central orchestration mechanism.

### Collection Backend (`src/dosctl/collections/`)
- `base.py` — `BaseCollection` ABC defining the collection interface
- `archive_org.py` — `ArchiveOrgCollection` base + `TotalDOSCollectionRelease14` concrete class
- `factory.py` — creates collection instances
- Game IDs are 8-character SHA1 hash prefixes derived from the game filename

### Platform Abstraction (`src/dosctl/lib/platform.py`)
- `PlatformBase` ABC for OS-specific paths and DOSBox detection
- `UnixPlatform`, `MacOSPlatform`, `WindowsPlatform` implementations
- `PlatformFactory` and `get_platform()` singleton

### DOSBox Launcher (`src/dosctl/lib/dosbox.py`)
- `DOSBoxLauncher` ABC and `StandardDOSBoxLauncher` using subprocess.Popen
- `get_dosbox_launcher()` singleton factory, `is_dosbox_available()`, `is_dosbox_installed()`
- Supports IPX networking via the `ipx` option (accepts `IPXServerConfig` or `IPXClientConfig`), which injects `-conf ipx.conf` and `IPXNET` commands

### IPX Networking (`src/dosctl/lib/network.py`)
- `IPXServerConfig` / `IPXClientConfig` dataclasses with `to_dosbox_command()` methods
- `get_local_ip()` helper for LAN IP detection
- `get_public_ip()` helper for public IP detection via external services

### Discovery Codes (`src/dosctl/lib/discovery.py`)
- Encodes IPv4 + port into human-friendly codes like `DOOM-3KF8A`
- 256-word list maps first IP byte to a word; remaining 3 bytes as base36
- `encode_discovery_code()`, `decode_discovery_code()`, `resolve_host()` (auto-detects raw IP vs code)
- Word list stored in `src/dosctl/lib/wordlist.txt` (8 words per line)

### UPnP Port Mapping (`src/dosctl/lib/upnp.py`)
- Stdlib-only UPnP IGD implementation for automatic router port forwarding
- SSDP discovery, SOAP port mapping, external IP retrieval
- `UPnPPortMapper` class with atexit cleanup of registered mappings

### Other Key Modules
- `config.py` — platform-aware directory paths (config, data, collections, downloads, installed)
- `lib/game.py` — game download, extraction, and installation
- `lib/config_store.py` — persists selected executables per game in JSON
- `lib/executables.py` — finds .exe/.com/.bat files in game directories; shared executable selection/prompting logic used by both play and net commands
- `lib/display.py` — terminal display formatting for game listings

## Conventions

- **Commits:** Conventional Commits format. `feat:` = minor bump, `fix:` = patch bump, `chore:` = no bump. See CONTRIBUTING.md.
- **Releases:** Automated via semantic-release on push to `main`. Updates version in both `pyproject.toml` and `src/dosctl/__init__.py`.
- **Python:** Requires >=3.8. Dependencies: click, requests, tqdm.
- **Testing:** pytest with unittest.mock. Tests use temporary directories for isolation.
- **Patterns:** Factory pattern for platform/collection/launcher. ABC for extensibility. Singletons for platform and launcher instances.
