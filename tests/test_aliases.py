"""Unit tests for dosctl.lib.aliases."""
import json
import pytest
from unittest.mock import patch
from dosctl.lib.aliases import (
    set_alias, remove_alias, list_aliases, resolve_game_id,
    _validate_alias,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _patch_aliases_file(tmp_path):
    """Return a context manager that redirects ALIASES_FILE to tmp_path."""
    return patch("dosctl.lib.aliases.ALIASES_FILE", tmp_path / "aliases.json")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class TestValidateAlias:
    @pytest.mark.parametrize("name", ["doom", "my-game", "game2", "a", "abc123"])
    def test_valid_names_do_not_raise(self, name):
        _validate_alias(name)  # should not raise

    @pytest.mark.parametrize("name", [
        "-badstart",   # starts with hyphen
        "UPPER",       # uppercase
        "has space",   # space
        "has_under",   # underscore
        "",            # empty
    ])
    def test_invalid_names_raise_value_error(self, name):
        with pytest.raises(ValueError):
            _validate_alias(name)


# ---------------------------------------------------------------------------
# Storage: set / list / remove
# ---------------------------------------------------------------------------

class TestAliasStorage:
    def test_set_creates_file(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345")
        assert (tmp_path / "aliases.json").exists()

    def test_set_persists_data(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345")
            aliases = list_aliases()
        assert aliases == {"doom": "abc12345"}

    def test_set_updates_existing_alias(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345")
            set_alias("doom", "deadbeef")
            aliases = list_aliases()
        assert aliases["doom"] == "deadbeef"

    def test_set_multiple_aliases(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345")
            set_alias("quake", "deadbeef")
            aliases = list_aliases()
        assert len(aliases) == 2
        assert aliases["doom"] == "abc12345"
        assert aliases["quake"] == "deadbeef"

    def test_remove_existing_alias(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345")
            remove_alias("doom")
            aliases = list_aliases()
        assert "doom" not in aliases

    def test_remove_nonexistent_alias_raises_key_error(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            with pytest.raises(KeyError):
                remove_alias("doesnotexist")

    def test_list_returns_empty_when_no_file(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            aliases = list_aliases()
        assert aliases == {}

    def test_list_returns_empty_on_corrupt_file(self, tmp_path):
        aliases_file = tmp_path / "aliases.json"
        aliases_file.write_text("not valid json {{{")
        with _patch_aliases_file(tmp_path):
            aliases = list_aliases()
        assert aliases == {}

    def test_file_is_sorted(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("zork", "aaaaaaaa")
            set_alias("doom", "bbbbbbbb")
        raw = json.loads((tmp_path / "aliases.json").read_text())
        assert list(raw.keys()) == sorted(raw.keys())


# ---------------------------------------------------------------------------
# resolve_game_id
# ---------------------------------------------------------------------------

class TestResolveGameId:
    def test_resolves_known_alias(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345")
            result = resolve_game_id("doom")
        assert result == "abc12345"

    def test_passthrough_for_unknown_value(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            result = resolve_game_id("abc12345")
        assert result == "abc12345"

    def test_passthrough_does_not_need_a_valid_game_id(self, tmp_path):
        """resolve_game_id never validates — it just looks up or passes through."""
        with _patch_aliases_file(tmp_path):
            result = resolve_game_id("anything-at-all")
        assert result == "anything-at-all"

    def test_resolves_after_update(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345")
            set_alias("doom", "deadbeef")
            result = resolve_game_id("doom")
        assert result == "deadbeef"

    def test_does_not_resolve_removed_alias(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345")
            remove_alias("doom")
            result = resolve_game_id("doom")
        assert result == "doom"  # passthrough, not the old game id
