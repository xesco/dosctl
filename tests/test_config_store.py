"""Tests for lib/config_store.py."""
import json
from unittest.mock import patch

from dosctl.lib.config_store import (
    load_play_config,
    save_play_config,
    get_game_command,
    set_game_command,
)


def _patch_files(tmp_path):
    config_file = tmp_path / "play_config.json"
    old_config_file = tmp_path / "run_config.json"
    return (
        patch("dosctl.lib.config_store.CONFIG_FILE", config_file),
        patch("dosctl.lib.config_store.OLD_CONFIG_FILE", old_config_file),
        config_file,
        old_config_file,
    )


class TestLoadPlayConfig:
    def test_returns_empty_dict_when_no_file(self, tmp_path):
        p1, p2, _, _ = _patch_files(tmp_path)
        with p1, p2:
            assert load_play_config() == {}

    def test_loads_existing_config(self, tmp_path):
        p1, p2, config_file, _ = _patch_files(tmp_path)
        config_file.write_text(json.dumps({"abc12345": "doom.exe"}))
        with p1, p2:
            assert load_play_config() == {"abc12345": "doom.exe"}

    def test_returns_empty_dict_on_corrupted_json(self, tmp_path):
        p1, p2, config_file, _ = _patch_files(tmp_path)
        config_file.write_text("not valid json{{{")
        with p1, p2:
            assert load_play_config() == {}

    def test_migrates_old_config_file(self, tmp_path):
        p1, p2, config_file, old_config_file = _patch_files(tmp_path)
        old_config_file.write_text(json.dumps({"xyz98765": "wolf3d.exe"}))
        with p1, p2:
            result = load_play_config()
        assert result == {"xyz98765": "wolf3d.exe"}
        assert config_file.exists()
        assert not old_config_file.exists()

    def test_does_not_migrate_when_new_file_exists(self, tmp_path):
        p1, p2, config_file, old_config_file = _patch_files(tmp_path)
        config_file.write_text(json.dumps({"new": "new.exe"}))
        old_config_file.write_text(json.dumps({"old": "old.exe"}))
        with p1, p2:
            assert load_play_config() == {"new": "new.exe"}
        assert old_config_file.exists()


class TestSetGameCommand:
    def test_saves_and_reads_command(self, tmp_path):
        p1, p2, config_file, _ = _patch_files(tmp_path)
        config_file.write_text(json.dumps({"abc12345": "old.exe"}))
        with p1, p2:
            set_game_command("abc12345", "new.exe")
            assert get_game_command("abc12345") == "new.exe"

    def test_removes_command_when_none(self, tmp_path):
        p1, p2, config_file, _ = _patch_files(tmp_path)
        config_file.write_text(json.dumps({"abc12345": "doom.exe"}))
        with p1, p2:
            set_game_command("abc12345", None)
            assert get_game_command("abc12345") is None

    def test_remove_nonexistent_is_noop(self, tmp_path):
        p1, p2, config_file, _ = _patch_files(tmp_path)
        config_file.write_text(json.dumps({}))
        with p1, p2:
            set_game_command("nope", None)
            assert load_play_config() == {}
