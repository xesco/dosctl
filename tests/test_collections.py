"""Tests for the collection architecture and TotalDOSCollectionRelease14."""
import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import tempfile
import shutil

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
        mock_response.text = "mock game list content"
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = TotalDOSCollectionRelease14(
                source="https://example.com/collection",
                cache_dir=temp_dir
            )
            
            collection.ensure_cache_is_present()
            
            # Check that the cache file was created
            cache_file = Path(temp_dir) / "games.txt"
            assert cache_file.exists()
            assert cache_file.read_text() == "mock game list content"

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
        mock_content = '''
        <a href="Game1%20(1990).zip">Game1 (1990).zip</a>
        <a href="Game2%20(1995).zip">Game2 (1995).zip</a>
        '''
        
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
            assert len(game1["id"]) == 8  # SHA1 hash truncated to 8 chars

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
            
            game = collection._find_game("abc12345")
            assert game is not None
            assert game["name"] == "Test Game"
            
            game = collection._find_game("notfound")
            assert game is None


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
