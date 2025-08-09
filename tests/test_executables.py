"""Tests for executable utilities."""
import pytest
from unittest.mock import patch, Mock
from pathlib import Path
import tempfile
import os

from dosctl.lib.executables import find_executables, executable_exists


class TestFindExecutables:
    """Test the find_executables function."""

    def test_find_executables_in_directory(self):
        """Test finding executables in a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some test files
            exe_file = temp_path / "game.exe"
            exe_file.write_text("fake exe")

            com_file = temp_path / "setup.com"
            com_file.write_text("fake com")

            bat_file = temp_path / "run.bat"
            bat_file.write_text("fake bat")

            txt_file = temp_path / "readme.txt"
            txt_file.write_text("not executable")

            executables = find_executables(temp_path)

            # Should find exe, com, and bat files
            assert len(executables) == 3
            assert "game.exe" in executables
            assert "setup.com" in executables
            assert "run.bat" in executables
            assert "readme.txt" not in executables

    def test_find_executables_case_insensitive(self):
        """Test that executable detection is case insensitive."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with different cases
            exe_file = temp_path / "GAME.EXE"
            exe_file.write_text("fake exe")

            com_file = temp_path / "Setup.COM"
            com_file.write_text("fake com")

            executables = find_executables(temp_path)

            assert len(executables) == 2
            assert "GAME.EXE" in executables
            assert "Setup.COM" in executables

    def test_find_executables_empty_directory(self):
        """Test finding executables in empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            executables = find_executables(temp_path)
            assert executables == []

    def test_find_executables_nonexistent_directory(self):
        """Test finding executables in nonexistent directory."""
        nonexistent_path = Path("/nonexistent/path")
        executables = find_executables(nonexistent_path)
        assert executables == []

    def test_find_executables_subdirectories_ignored(self):
        """Test that subdirectories are NOT ignored (recursive search)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create executable in main directory
            exe_file = temp_path / "main.exe"
            exe_file.write_text("fake exe")

            # Create subdirectory with executable
            sub_dir = temp_path / "subdir"
            sub_dir.mkdir()
            sub_exe = sub_dir / "sub.exe"
            sub_exe.write_text("fake sub exe")

            executables = find_executables(temp_path)

            # Should find both executables (recursive search)
            assert len(executables) == 2
            assert "main.exe" in executables
            assert "sub.exe" in executables


class TestExecutableExists:
    """Test the executable_exists function."""

    def test_executable_exists_true(self):
        """Test when executable exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            exe_file = temp_path / "game.exe"
            exe_file.write_text("fake exe")

            assert executable_exists(temp_path, "game.exe") is True

    def test_executable_exists_false(self):
        """Test when executable doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            assert executable_exists(temp_path, "nonexistent.exe") is False

    def test_executable_exists_case_sensitive(self):
        """Test case sensitive executable check."""
        import os
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            exe_file = temp_path / "GAME.EXE"
            exe_file.write_text("fake exe")

            # Should find exact case match
            assert executable_exists(temp_path, "GAME.EXE") is True

            # Check if filesystem is case sensitive
            test_file_lower = temp_path / "game.exe"
            is_case_sensitive = not test_file_lower.exists()

            if is_case_sensitive:
                # On case-sensitive filesystems, these should fail
                assert executable_exists(temp_path, "game.exe") is False
                assert executable_exists(temp_path, "Game.Exe") is False
            else:
                # On case-insensitive filesystems (like macOS default), these will succeed
                assert executable_exists(temp_path, "game.exe") is True
                assert executable_exists(temp_path, "Game.Exe") is True

    def test_executable_exists_non_executable_file(self):
        """Test with non-executable file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            txt_file = temp_path / "readme.txt"
            txt_file.write_text("not executable")

            assert executable_exists(temp_path, "readme.txt") is True  # File exists but is not considered "executable"

    def test_executable_exists_nonexistent_directory(self):
        """Test with nonexistent directory."""
        nonexistent_path = Path("/nonexistent/path")
        assert executable_exists(nonexistent_path, "game.exe") is False

    def test_executable_exists_directory_as_file(self):
        """Test when the executable name is actually a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            sub_dir = temp_path / "game.exe"
            sub_dir.mkdir()

            assert executable_exists(temp_path, "game.exe") is True  # Directory exists
