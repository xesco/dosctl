"""Tests for lib/collections_store.py."""
import json
from unittest.mock import patch

import pytest

import dosctl.lib.collections_store as store
from dosctl.lib.collections_store import (
    add_collection,
    cache_dir_for,
    env_override,
    get_active_name,
    list_collections,
    remove_collection,
    resolve_collection,
    set_active,
)


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.delenv("DOSCTL_COLLECTION", raising=False)
    monkeypatch.delenv("DOSCTL_COLLECTION_SOURCE", raising=False)
    with patch.object(store, "COLLECTIONS_FILE", tmp_path / "collections.json"), \
         patch.object(store, "CONFIG_DIR", tmp_path), \
         patch.object(store, "COLLECTION_CACHE_DIR", tmp_path / "cache"):
        yield tmp_path


class TestListAndActive:
    def test_builtin_only_by_default(self):
        assert list(list_collections()) == ["tdc"]
        assert list_collections()["tdc"]["type"] == "tdc_release_14"
        assert get_active_name() == "tdc"

    def test_add_and_list(self, isolated):
        add_collection("mine", "local_file", "/games")

        assert list(list_collections()) == ["tdc", "mine"]
        assert list_collections()["mine"] == {"type": "local_file", "source": "/games"}
        saved = json.loads((isolated / "collections.json").read_text())
        assert saved == {"active": "tdc", "collections": {"mine": {"type": "local_file", "source": "/games"}}}

    def test_set_active(self):
        add_collection("mine", "local_file", "/games")
        set_active("mine")

        assert get_active_name() == "mine"

    def test_set_active_unknown(self):
        with pytest.raises(KeyError):
            set_active("zzz")

    def test_active_falls_back_when_entry_is_gone(self, isolated):
        (isolated / "collections.json").write_text('{"active": "gone", "collections": {}}')

        assert get_active_name() == "tdc"

    def test_corrupt_file_is_treated_as_empty(self, isolated):
        (isolated / "collections.json").write_text("{not json")

        assert list(list_collections()) == ["tdc"]
        assert get_active_name() == "tdc"


class TestAddValidation:
    @pytest.mark.parametrize("name", ["Bad Name", "UPPER", "-lead", ""])
    def test_bad_name(self, name):
        with pytest.raises(ValueError, match="Invalid collection name"):
            add_collection(name, "local_file", "/games")

    def test_existing_name(self):
        add_collection("mine", "local_file", "/games")
        with pytest.raises(ValueError, match="already exists"):
            add_collection("mine", "local_file", "/other")

    def test_builtin_name(self):
        with pytest.raises(ValueError, match="already exists"):
            add_collection("tdc", "local_file", "/games")

    def test_unknown_type(self):
        with pytest.raises(ValueError, match="Unknown collection type"):
            add_collection("mine", "ftp", "/games")


class TestRemove:
    def test_remove_inactive(self):
        add_collection("mine", "local_file", "/games")

        assert remove_collection("mine") is False
        assert list(list_collections()) == ["tdc"]

    def test_remove_active_switches_to_builtin(self):
        add_collection("mine", "local_file", "/games")
        set_active("mine")

        assert remove_collection("mine") is True
        assert get_active_name() == "tdc"

    def test_remove_unknown(self):
        with pytest.raises(KeyError):
            remove_collection("zzz")

    def test_remove_builtin(self):
        with pytest.raises(ValueError, match="built in"):
            remove_collection("tdc")


class TestResolve:
    def test_builtin_uses_historical_cache_dir(self, isolated):
        resolved = resolve_collection()

        assert resolved.name == "tdc"
        assert resolved.type == "tdc_release_14"
        assert resolved.cache_dir == isolated / "cache"
        assert cache_dir_for("tdc") == isolated / "cache"

    def test_named_collection_gets_own_cache_dir(self, isolated):
        add_collection("mine", "local_file", "/games")
        set_active("mine")

        resolved = resolve_collection()

        assert resolved == ("mine", "local_file", "/games", isolated / "cache" / "mine")

    def test_env_overrides_active(self, isolated, monkeypatch):
        add_collection("mine", "local_file", "/games")
        set_active("mine")
        monkeypatch.setenv("DOSCTL_COLLECTION", "local_file")
        monkeypatch.setenv("DOSCTL_COLLECTION_SOURCE", "/env-games")

        assert env_override() == {"type": "local_file", "source": "/env-games"}
        assert resolve_collection() == ("env", "local_file", "/env-games", isolated / "cache" / "env")

    def test_env_source_alone_keeps_builtin_type(self, monkeypatch):
        monkeypatch.setenv("DOSCTL_COLLECTION_SOURCE", "https://example.com/items/x/y")

        assert resolve_collection().type == "tdc_release_14"
        assert resolve_collection().source == "https://example.com/items/x/y"

    def test_no_env_means_no_override(self):
        assert env_override() == {}
