"""Unit tests for dosctl.lib.aliases."""

import json
import pytest
from unittest.mock import patch
from dosctl.lib.aliases import (
    set_alias,
    remove_alias,
    remove_aliases_for_game_id,
    list_aliases,
    resolve_game_id,
    _validate_alias,
)


def _patch_aliases_file(tmp_path):
    return patch("dosctl.lib.aliases.ALIASES_FILE", tmp_path / "aliases.json")


class TestValidateAlias:
    @pytest.mark.parametrize("name", ["doom", "my-game", "game2", "a", "abc123"])
    def test_valid_names_do_not_raise(self, name):
        _validate_alias(name)

    @pytest.mark.parametrize("name", ["-badstart", "UPPER", "has space", "has_under", ""])
    def test_invalid_names_raise_value_error(self, name):
        with pytest.raises(ValueError):
            _validate_alias(name)


class TestAliasStorage:
    def test_set_persists_id_and_name(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345", "Doom (1993)")
            assert list_aliases() == {"doom": {"id": "abc12345", "name": "Doom (1993)"}}

    def test_set_updates_existing_alias(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345", "Doom (1993)")
            set_alias("doom", "deadbeef", "Doom II (1994)")
            assert list_aliases()["doom"] == {"id": "deadbeef", "name": "Doom II (1994)"}

    def test_set_multiple_aliases(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345", "Doom (1993)")
            set_alias("quake", "deadbeef", "Quake (1996)")
            aliases = list_aliases()
        assert len(aliases) == 2
        assert aliases["doom"] == {"id": "abc12345", "name": "Doom (1993)"}
        assert aliases["quake"] == {"id": "deadbeef", "name": "Quake (1996)"}

    def test_remove_existing_alias(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345", "Doom (1993)")
            remove_alias("doom")
            assert "doom" not in list_aliases()

    def test_remove_leaves_other_aliases_intact(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345", "Doom (1993)")
            set_alias("quake", "deadbeef", "Quake (1996)")
            remove_alias("doom")
            aliases = list_aliases()
        assert "doom" not in aliases
        assert aliases["quake"] == {"id": "deadbeef", "name": "Quake (1996)"}

    def test_remove_nonexistent_alias_raises_key_error(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            with pytest.raises(KeyError):
                remove_alias("doesnotexist")

    def test_remove_aliases_for_game_id(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345", "Doom (1993)")
            set_alias("doom-shareware", "abc12345", "Doom (1993)")
            set_alias("quake", "deadbeef", "Quake (1996)")
            removed = remove_aliases_for_game_id("abc12345")
            aliases = list_aliases()
        assert removed == ["doom", "doom-shareware"]
        assert "doom" not in aliases
        assert aliases["quake"] == {"id": "deadbeef", "name": "Quake (1996)"}

    def test_remove_aliases_for_game_id_returns_empty_when_no_match(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("quake", "deadbeef", "Quake (1996)")
            assert remove_aliases_for_game_id("abc12345") == []

    def test_list_returns_empty_when_no_file(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            assert list_aliases() == {}

    def test_list_returns_empty_on_corrupt_file(self, tmp_path):
        (tmp_path / "aliases.json").write_text("not valid json {{{")
        with _patch_aliases_file(tmp_path):
            assert list_aliases() == {}

    def test_file_is_sorted(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("zork", "aaaaaaaa", "Zork (1980)")
            set_alias("doom", "bbbbbbbb", "Doom (1993)")
        raw = json.loads((tmp_path / "aliases.json").read_text())
        assert list(raw.keys()) == sorted(raw.keys())


class TestResolveGameId:
    def test_resolves_known_alias(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345", "Doom (1993)")
            assert resolve_game_id("doom") == "abc12345"

    def test_passthrough_for_unknown_value(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            assert resolve_game_id("abc12345") == "abc12345"

    def test_resolves_after_update(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345", "Doom (1993)")
            set_alias("doom", "deadbeef", "Doom II (1994)")
            assert resolve_game_id("doom") == "deadbeef"

    def test_does_not_resolve_removed_alias(self, tmp_path):
        with _patch_aliases_file(tmp_path):
            set_alias("doom", "abc12345", "Doom (1993)")
            remove_alias("doom")
            assert resolve_game_id("doom") == "doom"
