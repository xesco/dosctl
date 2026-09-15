"""Tests for the collection architecture and TotalDOSCollection backends."""
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from dosctl.collections.archive_org import TotalDOSCollectionRelease14


class TestArchiveOrgCollection:
    """Test the base ArchiveOrgCollection class."""

    def test_init(self):
        """Test collection initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )

            assert collection.source == "https://example.com/collection"
            assert collection.collection_name == "Total DOS Collection Release 14"
            assert collection.cache_dir == Path(temp_dir)
            assert collection._games_data == []

    def test_parse_filename_with_year(self):
        """Test filename parsing with year."""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )

            result = collection._parse_filename("Doom (1993)(id Software).zip")
            assert result["name"] == "Doom (1993)(id Software)"
            assert result["year"] == "1993"

    def test_parse_filename_without_year(self):
        """Test filename parsing without year."""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )

            result = collection._parse_filename("SomeGame.zip")
            assert result["name"] == "SomeGame"
            assert result["year"] is None

    @patch('requests.get')
    def test_ensure_cache_is_present_downloads_when_missing(self, mock_get):
        """Test that cache is downloaded when missing."""
        mock_response = Mock()
        mock_response.text = '<a href="Game1%20(1990).zip">Game1 (1990).zip</a>'
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as temp_dir:
            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )

            collection.ensure_cache_is_present()

            # Check that the cache file was created as TSV
            cache_file = Path(temp_dir) / "games.txt"
            assert cache_file.exists()
            assert cache_file.read_text() == "18800512\tGame1 (1990)\t1990\tGame1 (1990).zip\n"

    def test_ensure_cache_is_present_skips_when_exists(self):
        """Test that cache download is skipped when file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "games.txt"
            cache_file.write_text("existing content")

            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )

            with patch('requests.get') as mock_get:
                collection.ensure_cache_is_present()
                mock_get.assert_not_called()

    def test_build_download_url(self):
        """Test URL building for Release 14."""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = TotalDOSCollectionRelease14(
                source="https://ia800906.us.archive.org/view_archive.php?archive=/4/items/Total_DOS_Collection_Release_14/TDC_Release_14.zip",
                cache_dir=temp_dir
            )

            url = collection._build_download_url("Some%20Game.zip")
            expected = "https://archive.org/download/Total_DOS_Collection_Release_14/TDC_Release_14.zip/Some%20Game.zip"
            assert url == expected

    def test_populate_games_data(self):
        """Test game data population from cache."""
        mock_content = "18800512\tGame1 (1990)\t1990\tGame1 (1990).zip\n20210409\tGame2 (1995)\t1995\tGame2 (1995).zip\n"

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "games.txt"
            cache_file.write_text(mock_content)

            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )

            collection._populate_games_data()

            assert len(collection._games_data) == 2

            game1 = collection._games_data[0]
            assert game1["name"] == "Game1 (1990)"
            assert game1["year"] == "1990"
            assert game1["full_path"] == "Game1 (1990).zip"
            assert game1["id"] == "18800512"

    def test_find_game(self):
        """Test finding a game by ID."""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )

            # Manually populate some test data
            collection._games_data = [
                {"id": "abc12345", "name": "Test Game", "year": "1990", "full_path": "test.zip"}
            ]

            game = collection.find_game("abc12345")
            assert game is not None
            assert game["name"] == "Test Game"

            game = collection.find_game("notfound")
            assert game is None

    def test_find_game_builds_and_reuses_index(self):
        """find_game builds an id->game index once and reuses it (O(1) lookups)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir,
            )

            collection._games_data = [
                {"id": "aaaa1111", "name": "Alpha", "year": "1990", "full_path": "a.zip"},
                {"id": "bbbb2222", "name": "Beta", "year": "1992", "full_path": "b.zip"},
            ]

            # First lookup builds the index over all games.
            assert collection.find_game("bbbb2222")["name"] == "Beta"
            assert set(collection._games_index) == {"aaaa1111", "bbbb2222"}

            # A second lookup reuses the same index object instead of rebuilding.
            index_after_first = collection._games_index
            assert collection.find_game("aaaa1111")["name"] == "Alpha"
            assert collection._games_index is index_after_first

            assert collection.find_game("missing") is None

    def test_find_game_index_invalidated_on_repopulate(self):
        """Re-populating the cache rebuilds the index so lookups stay correct."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "games.txt"
            cache_file.write_text("11111111\tOld Game\t1990\told.zip\n")

            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir,
            )

            collection._populate_games_data()
            assert collection.find_game("11111111")["name"] == "Old Game"

            # The cache changes (e.g. after a refresh) and data is re-populated.
            cache_file.write_text(
                "22222222\tNew One\t1995\tnew1.zip\n"
                "33333333\tNew Two\t1996\tnew2.zip\n"
            )
            collection._populate_games_data()

            assert collection.find_game("11111111") is None
            assert collection.find_game("22222222")["name"] == "New One"
            assert collection.find_game("33333333")["name"] == "New Two"

    @patch("requests.get")
    def test_download_game_rejects_truncated_download(self, mock_get):
        """A short read vs. content-length is rejected and the partial file removed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = TotalDOSCollectionRelease14(
                source="https://ia800906.us.archive.org/view_archive.php?archive=/4/items/Total_DOS_Collection_Release_14/TDC_Release_14.zip",
                cache_dir=temp_dir,
            )
            collection._games_data = [
                {"id": "test123", "name": "Test Game", "year": "1990", "full_path": "TestGame.zip"}
            ]

            # Server promises 100 bytes but the stream only delivers 6.
            mock_response = Mock()
            mock_response.raise_for_status = Mock()
            mock_response.headers = {"content-length": "100"}
            mock_response.iter_content = Mock(return_value=[b"only 6"])
            mock_response.__enter__ = Mock(return_value=mock_response)
            mock_response.__exit__ = Mock(return_value=None)
            mock_get.return_value = mock_response

            downloads_dir = Path(temp_dir) / "downloads"
            result = collection.download_game("test123", str(downloads_dir))

            assert result is None
            assert not (downloads_dir / "Test Game.zip").exists()

    def test_unzip_game_rejects_unsafe_paths(self):
        """Unsafe ZIP entries should be rejected before they hit the install dir."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            downloads_dir = temp_path / "downloads"
            downloads_dir.mkdir()
            install_path = temp_path / "installed" / "test123"
            outside_path = temp_path / "evil.txt"

            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )
            collection._games_data = [{
                "id": "test123",
                "name": "Test Game",
                "year": "1990",
                "full_path": "TestGame.zip",
            }]

            zip_path = downloads_dir / "Test Game.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("GOOD.EXE", "good")
                zf.writestr("../evil.txt", "bad")

            with pytest.raises(ValueError, match="unsafe path"):
                collection.unzip_game("test123", downloads_dir, install_path)

            assert not install_path.exists()
            assert not outside_path.exists()

    def test_unzip_game_extracts_symlink_entries_as_regular_files(self):
        """Symlink-flagged entries should be extracted as regular files (common in DOS ZIPs)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            downloads_dir = temp_path / "downloads"
            downloads_dir.mkdir()
            install_path = temp_path / "installed" / "test123"

            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )
            collection._games_data = [{
                "id": "test123",
                "name": "Test Game",
                "year": "1990",
                "full_path": "TestGame.zip",
            }]

            zip_path = downloads_dir / "Test Game.zip"
            with zipfile.ZipFile(zip_path, "w") as zf:
                zf.writestr("GOOD.EXE", "good")
                symlink_info = zipfile.ZipInfo("GAME.EXE")
                symlink_info.create_system = 3
                symlink_info.external_attr = 0o120777 << 16
                zf.writestr(symlink_info, "fake symlink content")

            collection.unzip_game("test123", downloads_dir, install_path)

            assert install_path.exists()
            assert (install_path / "GOOD.EXE").read_text() == "good"
            assert (install_path / "GAME.EXE").read_text() == "fake symlink content"


class TestCollectionFactory:
    """Test the collection factory."""

    def test_create_collection_success(self):
        """Test successful collection creation."""
        from dosctl.collections.factory import create_collection

        with tempfile.TemporaryDirectory() as temp_dir:
            collection = create_collection(
                "tdc_release_14",
                "https://example.com/source",
                temp_dir
            )

            assert isinstance(collection, TotalDOSCollectionRelease14)
            assert collection.source == "https://example.com/source"

    def test_create_collection_invalid_type(self):
        """Test creation with invalid collection type."""
        from dosctl.collections.factory import create_collection

        with pytest.raises(ValueError, match="Unknown collection type"):
            create_collection("invalid_type", "source", "cache_dir")

    def test_get_available_collections(self):
        """Test getting available collection types."""
        from dosctl.collections.factory import get_available_collections

        available = get_available_collections()
        assert "tdc_release_14" in available
        assert len(available) >= 1
