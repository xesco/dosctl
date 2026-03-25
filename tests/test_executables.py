"""Tests for executable utilities."""
from pathlib import Path
import tempfile

from dosctl.lib.executables import find_executables, executable_exists


class TestFindExecutables:
    def test_finds_exe_com_bat_but_not_other_extensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "game.exe").write_text("")
            (temp_path / "setup.com").write_text("")
            (temp_path / "run.bat").write_text("")
            (temp_path / "readme.txt").write_text("")
            result = find_executables(temp_path)
        assert sorted(result) == sorted(["game.exe", "setup.com", "run.bat"])

    def test_case_insensitive(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "GAME.EXE").write_text("")
            (temp_path / "Setup.COM").write_text("")
            result = find_executables(temp_path)
        assert "GAME.EXE" in result
        assert "Setup.COM" in result

    def test_returns_empty_for_empty_or_nonexistent_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            assert find_executables(Path(temp_dir)) == []
        assert find_executables(Path("/nonexistent/path")) == []

    def test_includes_subdirectory_executables(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "main.exe").write_text("")
            sub = temp_path / "subdir"
            sub.mkdir()
            (sub / "sub.exe").write_text("")
            result = find_executables(temp_path)
        assert "main.exe" in result
        assert "subdir/sub.exe" in result


class TestExecutableExists:
    def test_returns_true_when_file_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "game.exe").write_text("")
            assert executable_exists(temp_path, "game.exe") is True

    def test_returns_false_when_file_missing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            assert executable_exists(Path(temp_dir), "nonexistent.exe") is False

    def test_returns_false_for_nonexistent_directory(self):
        assert executable_exists(Path("/nonexistent/path"), "game.exe") is False

    def test_case_sensitive_on_current_filesystem(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            (temp_path / "GAME.EXE").write_text("")
            assert executable_exists(temp_path, "GAME.EXE") is True
            is_case_sensitive = not (temp_path / "game.exe").exists()
            if is_case_sensitive:
                assert executable_exists(temp_path, "game.exe") is False
