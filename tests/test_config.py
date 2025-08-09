"""Tests for configuration management."""
import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import tempfile
import os

from dosctl.config import ensure_dirs_exist, DOWNLOADS_DIR, INSTALLED_DIR, CONFIG_DIR, DATA_DIR, COLLECTION_CACHE_DIR


class TestConfigModule:
    """Test the config module functions and constants."""

    def test_downloads_dir_constant(self):
        """Test that DOWNLOADS_DIR is properly defined."""
        assert DOWNLOADS_DIR is not None
        assert isinstance(DOWNLOADS_DIR, Path)
        assert str(DOWNLOADS_DIR).endswith("dosctl/downloads")

    def test_installed_dir_constant(self):
        """Test that INSTALLED_DIR is properly defined."""
        assert INSTALLED_DIR is not None
        assert isinstance(INSTALLED_DIR, Path)
        assert str(INSTALLED_DIR).endswith("dosctl/installed")

    def test_ensure_dirs_exist_creates_missing_directories(self):
        """Test that ensure_dirs_exist creates missing directories."""
        # Since we're using platform-specific directories, let's just test
        # that the function works without error and the directories exist after
        try:
            ensure_dirs_exist()
            # If we get here without exception, the function worked
            assert True

            # Check that the directories now exist
            assert CONFIG_DIR.exists()
            assert DATA_DIR.exists()
            assert DOWNLOADS_DIR.exists()
            assert INSTALLED_DIR.exists()
            assert COLLECTION_CACHE_DIR.exists()
        except Exception as e:
            pytest.fail(f"ensure_dirs_exist() raised an exception: {e}")

    @patch('dosctl.config.DOWNLOADS_DIR')
    @patch('dosctl.config.INSTALLED_DIR')
    def test_ensure_dirs_exist_skips_existing_directories(self, mock_installed, mock_downloads):
        """Test that ensure_dirs_exist doesn't recreate existing directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create directories first
            mock_downloads_path = temp_path / "downloads"
            mock_installed_path = temp_path / "installed"
            mock_downloads_path.mkdir()
            mock_installed_path.mkdir()

            # Set up mock paths
            mock_downloads.return_value = mock_downloads_path
            mock_installed.return_value = mock_installed_path

            # Configure the mocks to return the paths
            mock_downloads.__fspath__ = lambda: str(mock_downloads_path)
            mock_installed.__fspath__ = lambda: str(mock_installed_path)

            # Get initial modification times
            downloads_mtime = mock_downloads_path.stat().st_mtime
            installed_mtime = mock_installed_path.stat().st_mtime

            # Call the function
            ensure_dirs_exist()

            # Check that directories still exist and weren't modified
            assert mock_downloads_path.exists()
            assert mock_installed_path.exists()
            assert mock_downloads_path.stat().st_mtime == downloads_mtime
            assert mock_installed_path.stat().st_mtime == installed_mtime

    def test_ensure_dirs_exist_handles_permission_errors(self):
        """Test that ensure_dirs_exist handles permission errors gracefully."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            mock_mkdir.side_effect = PermissionError("Permission denied")

            # Should not raise an exception
            try:
                ensure_dirs_exist()
                # If we get here, the function handled the error gracefully
                # or the directories already existed
            except PermissionError:
                pytest.fail("ensure_dirs_exist should handle PermissionError gracefully")

    def test_paths_are_absolute(self):
        """Test that directory paths are absolute."""
        assert DOWNLOADS_DIR.is_absolute()
        assert INSTALLED_DIR.is_absolute()

    def test_paths_point_to_different_directories(self):
        """Test that downloads and installed directories are different."""
        assert DOWNLOADS_DIR != INSTALLED_DIR
        assert str(DOWNLOADS_DIR) != str(INSTALLED_DIR)
