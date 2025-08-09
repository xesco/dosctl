"""Integration tests for dosctl functionality."""
import pytest
from unittest.mock import patch, Mock, mock_open
from pathlib import Path
import tempfile
import shutil
import zipfile

from dosctl.collections.factory import create_collection
from dosctl.lib.game import install_game
from dosctl.lib import game as game_module
from pathlib import Path
import tempfile
import shutil
import zipfile

from dosctl.collections.factory import create_collection
from dosctl.lib.game import install_game


class TestIntegration:
    """Integration tests covering end-to-end functionality."""

    def test_game_installation_workflow(self):
        """Test the complete game installation workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "downloads"
            installed_dir = Path(temp_dir) / "installed"
            cache_dir = Path(temp_dir) / "cache"

            # Create directories
            downloads_dir.mkdir()
            installed_dir.mkdir()
            cache_dir.mkdir()

            # Patch the constants directly in the game module
            with patch.object(game_module, 'DOWNLOADS_DIR', downloads_dir), \
                 patch.object(game_module, 'INSTALLED_DIR', installed_dir):

                # Create a mock collection with test data
                collection = create_collection(
                    "tdc_release_14",
                    "https://example.com/source",
                    str(cache_dir)
                )

                # Add test game data
                collection._games_data = [{
                    "id": "test123",
                    "name": "Test Game",
                    "year": "1990",
                    "full_path": "TestGame.zip"
                }]

                # Create a mock zip file with game content
                zip_path = downloads_dir / "Test Game.zip"  # Use the actual game name with space
                with zipfile.ZipFile(zip_path, 'w') as zf:
                    zf.writestr("GAME.EXE", "fake game executable")
                    zf.writestr("README.TXT", "Game instructions")
                    zf.writestr("DATA/LEVEL1.DAT", "game data")

                # Mock the download method to return our zip file
                with patch.object(collection, 'download_game', return_value=str(zip_path)):
                    # Test game installation
                    game, install_path = install_game(collection, "test123")

                    assert game is not None
                    assert game["name"] == "Test Game"
                    assert install_path == installed_dir / "test123"

                    # Check that files were extracted
                    assert install_path.exists()
                    assert (install_path / "GAME.EXE").exists()
                    assert (install_path / "README.TXT").exists()
                    assert (install_path / "DATA" / "LEVEL1.DAT").exists()

    def test_collection_game_search_workflow(self):
        """Test searching for games in a collection."""
        mock_content = '''
        <a href="Doom%20(1993)(id%20Software).zip">Doom (1993)(id Software).zip</a>
        <a href="Quake%20(1996)(id%20Software).zip">Quake (1996)(id Software).zip</a>
        <a href="Wolfenstein%203D%20(1992)(id%20Software).zip">Wolfenstein 3D (1992)(id Software).zip</a>
        '''

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "games.txt"
            cache_file.write_text(mock_content)

            collection = create_collection(
                "tdc_release_14",
                "https://example.com/source",
                temp_dir
            )

            # Populate the collection data
            collection._populate_games_data()

            # Test getting all games
            all_games = collection.get_games()
            assert len(all_games) == 3

            # Test finding specific games by searching through results
            doom_games = [g for g in all_games if "doom" in g["name"].lower()]
            assert len(doom_games) == 1
            assert doom_games[0]["name"] == "Doom (1993)(id Software)"
            assert doom_games[0]["year"] == "1993"

            id_games = [g for g in all_games if "id software" in g["name"].lower()]
            assert len(id_games) == 3  # All games are by id Software

    def test_cache_management_workflow(self):
        """Test cache creation and management."""
        with tempfile.TemporaryDirectory() as temp_dir:
            collection = create_collection(
                "tdc_release_14",
                "https://example.com/source",
                temp_dir
            )

            cache_file = Path(temp_dir) / "games.txt"

            # Initially no cache
            assert not cache_file.exists()

            # Mock successful HTTP request
            with patch('requests.get') as mock_get:
                mock_response = Mock()
                mock_response.text = "<a href='game.zip'>game.zip</a>"
                mock_response.raise_for_status = Mock()
                mock_get.return_value = mock_response

                collection.ensure_cache_is_present()

                # Cache should now exist
                assert cache_file.exists()
                assert cache_file.read_text() == "<a href='game.zip'>game.zip</a>"

    def test_error_handling_workflow(self):
        """Test various error conditions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "downloads"
            installed_dir = Path(temp_dir) / "installed"

            downloads_dir.mkdir()
            installed_dir.mkdir()

            # Patch the constants directly in the game module
            with patch.object(game_module, 'DOWNLOADS_DIR', downloads_dir), \
                 patch.object(game_module, 'INSTALLED_DIR', installed_dir):

                collection = create_collection(
                    "tdc_release_14",
                    "https://example.com/source",
                    temp_dir
                )

                # Test installing non-existent game
                with pytest.raises(FileNotFoundError):
                    install_game(collection, "nonexistent123")

    def test_game_data_persistence(self):
        """Test that game data persists across operations."""
        mock_content = '''
        <a href="TestGame%20(1990).zip">TestGame (1990).zip</a>
        '''

        with tempfile.TemporaryDirectory() as temp_dir:
            cache_file = Path(temp_dir) / "games.txt"
            cache_file.write_text(mock_content)

            collection = create_collection(
                "tdc_release_14",
                "https://example.com/source",
                temp_dir
            )

            # Populate the collection data
            collection._populate_games_data()

            # Test that game data is accessible
            games = collection.get_games()
            assert len(games) == 1

            game = games[0]
            assert game["name"] == "TestGame (1990)"
            assert game["year"] == "1990"
            assert len(game["id"]) == 8  # SHA1 hash truncated to 8 chars

    def test_collection_download_integration(self):
        """Test collection download functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            downloads_dir = Path(temp_dir) / "downloads"
            downloads_dir.mkdir()

            # Patch the constants directly in the game module
            with patch.object(game_module, 'DOWNLOADS_DIR', downloads_dir):

                collection = create_collection(
                    "tdc_release_14",
                    "https://ia800906.us.archive.org/view_archive.php?archive=/4/items/Total_DOS_Collection_Release_14/TDC_Release_14.zip",
                    temp_dir
                )

                # Add test game data
                collection._games_data = [{
                    "id": "test123",
                    "name": "Test Game",
                    "year": "1990",
                    "full_path": "TestGame.zip"
                }]

                # Mock the HTTP request for download
                mock_content = b"fake zip content"
                with patch('requests.get') as mock_get:
                    mock_response = Mock()
                    mock_response.content = mock_content
                    mock_response.raise_for_status = Mock()
                    mock_response.headers = {'content-length': str(len(mock_content))}
                    mock_response.iter_content = Mock(return_value=[mock_content])
                    mock_response.__enter__ = Mock(return_value=mock_response)
                    mock_response.__exit__ = Mock(return_value=None)
                    mock_get.return_value = mock_response

                    # Test download
                    download_path = collection.download_game("test123", str(downloads_dir))

                    assert download_path is not None
                    assert Path(download_path).exists()
                    assert Path(download_path).read_bytes() == mock_content
