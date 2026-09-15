"""Named collections in CONFIG_DIR/collections.json, and which one is active."""

import json
import os
import re
from pathlib import Path
from typing import Dict, NamedTuple

import click

from dosctl.collections.factory import get_available_collections
from dosctl.config import COLLECTION_CACHE_DIR, CONFIG_DIR, TDC_RELEASE_14_SOURCE

COLLECTIONS_FILE = CONFIG_DIR / "collections.json"
BUILTIN_NAME = "tdc"
BUILTIN = {"type": "tdc14", "source": TDC_RELEASE_14_SOURCE}
ENV_NAME = "env"
_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*$")


class ResolvedCollection(NamedTuple):
    name: str
    type: str
    source: str
    cache_dir: Path


def _validate_name(name: str) -> None:
    if not _NAME_RE.match(name):
        raise ValueError(
            f"Invalid collection name '{name}'. "
            "Names must start with a letter or digit and contain only "
            "lowercase letters, digits, and hyphens."
        )


def _load() -> Dict:
    if not COLLECTIONS_FILE.exists():
        return {"active": BUILTIN_NAME, "collections": {}}
    try:
        with open(COLLECTIONS_FILE) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"active": BUILTIN_NAME, "collections": {}}
    data.setdefault("active", BUILTIN_NAME)
    data.setdefault("collections", {})
    return data


def _save(data: Dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(COLLECTIONS_FILE, "w") as f:
            json.dump(data, f, indent=2, sort_keys=True)
    except OSError as e:
        click.echo(f"Warning: Could not save collections: {e}", err=True)


def list_collections() -> Dict[str, Dict[str, str]]:
    """Return every collection as {name: {"type": ..., "source": ...}}, the built-in first."""
    return {BUILTIN_NAME: dict(BUILTIN), **_load()["collections"]}


def get_active_name() -> str:
    """Return the name of the active collection; falls back to the built-in when it is gone."""
    data = _load()
    if data["active"] in list_collections():
        return data["active"]
    return BUILTIN_NAME


def add_collection(name: str, collection_type: str, source: str) -> None:
    """Store a collection. Raises ValueError for a bad name, type, or a name in use."""
    _validate_name(name)
    if name in list_collections():
        raise ValueError(f"A collection named '{name}' already exists.")
    if collection_type not in get_available_collections():
        available = ", ".join(get_available_collections())
        raise ValueError(f"Unknown collection type '{collection_type}'. Available: {available}")
    data = _load()
    data["collections"][name] = {"type": collection_type, "source": source}
    _save(data)


def set_active(name: str) -> None:
    """Make name the active collection. Raises KeyError when it does not exist."""
    if name not in list_collections():
        raise KeyError(name)
    data = _load()
    data["active"] = name
    _save(data)


def remove_collection(name: str) -> bool:
    """Remove a stored collection; returns True when it was the active one.

    Raises KeyError when it does not exist and ValueError for the built-in.
    """
    if name == BUILTIN_NAME:
        raise ValueError(f"'{BUILTIN_NAME}' is built in and cannot be removed.")
    data = _load()
    if name not in data["collections"]:
        raise KeyError(name)
    del data["collections"][name]
    was_active = data["active"] == name
    if was_active:
        data["active"] = BUILTIN_NAME
    _save(data)
    return was_active


def cache_dir_for(name: str) -> Path:
    """The built-in keeps the historical cache directory; every other name gets its own."""
    if name == BUILTIN_NAME:
        return COLLECTION_CACHE_DIR
    return COLLECTION_CACHE_DIR / name


def env_override() -> Dict[str, str]:
    """The collection set by DOSCTL_COLLECTION / DOSCTL_COLLECTION_SOURCE, or {} when unset."""
    collection_type = os.environ.get("DOSCTL_COLLECTION")
    source = os.environ.get("DOSCTL_COLLECTION_SOURCE")
    if not collection_type and not source:
        return {}
    return {
        "type": collection_type or BUILTIN["type"],
        "source": source or BUILTIN["source"],
    }


def resolve_collection() -> ResolvedCollection:
    """The collection commands read: the environment override, else the active one."""
    override = env_override()
    if override:
        return ResolvedCollection(ENV_NAME, override["type"], override["source"], cache_dir_for(ENV_NAME))
    name = get_active_name()
    entry = list_collections()[name]
    return ResolvedCollection(name, entry["type"], entry["source"], cache_dir_for(name))
