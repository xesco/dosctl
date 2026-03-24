"""Tests for the collection architecture and TotalDOSCollectionRelease14."""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import tempfile
import shutil
import zipfile

from dosctl.collections.archive_org import ArchiveOrgCollection, TotalDOSCollectionRelease14


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
