"""CLI tests for the col command."""
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

import dosctl.lib.collections_store as store
from dosctl.main import cli


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.delenv("DOSCTL_COLLECTION", raising=False)
    monkeypatch.delenv("DOSCTL_COLLECTION_SOURCE", raising=False)
    with patch.object(store, "COLLECTIONS_FILE", tmp_path / "collections.json"), \
         patch.object(store, "CONFIG_DIR", tmp_path), \
         patch.object(store, "COLLECTION_CACHE_DIR", tmp_path / "cache"):
        yield tmp_path


@pytest.fixture
def games_dir(tmp_path):
    d = tmp_path / "games"
    d.mkdir()
    return d


def run(*args):
    return CliRunner().invoke(cli, ["col", *args])


class TestAdd:
    def test_add_directory(self, games_dir):
        result = run("add", "mine", str(games_dir))

        assert result.exit_code == 0
        assert result.output == (
            f"Collection 'mine' (local_file) added: {games_dir.resolve()}\n"
            "Use 'dosctl col use mine' to switch to it.\n"
        )
        assert store.list_collections()["mine"] == {"type": "local_file", "source": str(games_dir.resolve())}

    def test_add_expands_home(self, games_dir, monkeypatch):
        monkeypatch.setenv("HOME", str(games_dir.parent))

        result = run("add", "mine", "~/games")

        assert result.exit_code == 0
        assert store.list_collections()["mine"]["source"] == str(games_dir.resolve())

    def test_add_url_defaults_to_tdc_type(self):
        result = run("add", "other", "https://example.com/items/x/y")

        assert result.exit_code == 0
        assert store.list_collections()["other"] == {
            "type": "tdc_release_14", "source": "https://example.com/items/x/y",
        }

    def test_add_explicit_type(self, games_dir):
        result = run("add", "-t", "local_file", "mine", str(games_dir))

        assert result.exit_code == 0
        assert store.list_collections()["mine"]["type"] == "local_file"

    def test_add_missing_directory(self, tmp_path):
        result = run("add", "mine", str(tmp_path / "nope"))

        assert f"Error: Directory '{tmp_path / 'nope'}' not found." in result.output
        assert "mine" not in store.list_collections()

    def test_add_bad_name(self, games_dir):
        result = run("add", "Bad Name", str(games_dir))

        assert "Error: Invalid collection name 'Bad Name'" in result.output

    def test_add_existing_name(self, games_dir):
        run("add", "mine", str(games_dir))

        result = run("add", "mine", str(games_dir))

        assert "Error: A collection named 'mine' already exists." in result.output


class TestUse:
    def test_use(self, games_dir):
        run("add", "mine", str(games_dir))

        result = run("use", "mine")

        assert result.output == "Now using collection 'mine'.\n"
        assert store.get_active_name() == "mine"

    def test_use_unknown(self):
        result = run("use", "zzz")

        assert result.output == "Error: No collection 'zzz' found.\n"

    def test_commands_read_the_active_collection(self, games_dir):
        run("add", "mine", str(games_dir))
        run("use", "mine")
        mock_collection = MagicMock()

        with patch("dosctl.lib.decorators.create_collection", return_value=mock_collection) as create:
            CliRunner().invoke(cli, ["list"])

        create.assert_called_once_with(
            "local_file", source=str(games_dir.resolve()), cache_dir=store.COLLECTION_CACHE_DIR / "mine",
        )


class TestList:
    def test_list_marks_active(self, games_dir):
        run("add", "mine", str(games_dir))
        run("use", "mine")

        result = run("list")

        lines = result.output.splitlines()
        assert lines[0] == "Collections:"
        assert lines[1].startswith("  tdc   tdc_release_14  https://")
        assert lines[2] == f"* mine  local_file      {games_dir.resolve()}"

    def test_list_notes_env_override(self, monkeypatch):
        monkeypatch.setenv("DOSCTL_COLLECTION", "local_file")
        monkeypatch.setenv("DOSCTL_COLLECTION_SOURCE", "/env-games")

        result = run("list")

        assert result.output.splitlines()[-1] == "DOSCTL_COLLECTION overrides this: local_file /env-games"


class TestRemove:
    def test_remove(self, games_dir, isolated):
        run("add", "mine", str(games_dir))
        cache = isolated / "cache" / "mine"
        cache.mkdir(parents=True)
        (cache / "games.txt").write_text("x")

        result = run("remove", "mine")

        assert result.output == "Collection 'mine' removed.\n"
        assert "mine" not in store.list_collections()
        assert not cache.exists()

    def test_remove_active_switches_back(self, games_dir):
        run("add", "mine", str(games_dir))
        run("use", "mine")

        result = run("remove", "mine")

        assert result.output == "Collection 'mine' removed.\nNow using collection 'tdc'.\n"
        assert store.get_active_name() == "tdc"

    def test_remove_builtin(self):
        result = run("remove", "tdc")

        assert result.output == "Error: 'tdc' is built in and cannot be removed.\n"

    def test_remove_unknown(self):
        result = run("remove", "zzz")

        assert result.output == "Error: No collection 'zzz' found.\n"
