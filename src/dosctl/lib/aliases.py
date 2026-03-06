"""Alias storage for game IDs.

Aliases are persisted to CONFIG_DIR/aliases.json and allow users to refer
to games by a memorable name instead of an 8-character hash ID.
"""

import json
import re
from typing import Dict

from dosctl.config import CONFIG_DIR

ALIASES_FILE = CONFIG_DIR / "aliases.json"
_ALIAS_RE = re.compile(r'^[a-z0-9][a-z0-9\-]*$')


def _validate_alias(alias: str) -> None:
    """Raise ValueError if alias contains invalid characters."""
    if not _ALIAS_RE.match(alias):
        raise ValueError(
            f"Invalid alias '{alias}'. "
            "Aliases must start with a letter or digit and contain only "
            "lowercase letters, digits, and hyphens."
        )


def _load() -> Dict:
    if not ALIASES_FILE.exists():
        return {}
    try:
        with open(ALIASES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save(aliases: Dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(ALIASES_FILE, "w") as f:
            json.dump(aliases, f, indent=2, sort_keys=True)
    except OSError as e:
        print(f"Warning: Could not save aliases: {e}")


def set_alias(alias: str, game_id: str, game_name: str) -> None:
    """Create or update an alias pointing to game_id, storing game_name."""
    _validate_alias(alias)
    aliases = _load()
    aliases[alias] = {"id": game_id, "name": game_name}
    _save(aliases)


def remove_alias(alias: str) -> None:
    """Remove an alias. Raises KeyError if it does not exist."""
    aliases = _load()
    if alias not in aliases:
        raise KeyError(alias)
    del aliases[alias]
    _save(aliases)


def list_aliases() -> Dict[str, Dict[str, str]]:
    """Return all aliases as {alias: {"id": game_id, "name": game_name}}."""
    return _load()


def resolve_game_id(value: str) -> str:
    """Return the game ID for value.

    If value matches a known alias the associated game ID is returned.
    Otherwise value is returned unchanged, so raw 8-char IDs keep working.
    """
    aliases = _load()
    entry = aliases.get(value)
    if entry is None:
        return value
    return entry["id"]
