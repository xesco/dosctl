"""Tests for the display utilities."""
import pytest
from unittest.mock import patch, Mock
from io import StringIO

from dosctl.lib.display import sort_games, display_games


class TestSortGames:
    """Test the sort_games function."""
    
    def test_sort_by_name_ascending(self):
        """Test sorting by name in ascending order."""
        games = [
            {"name": "Zebra Game", "year": "1990"},
            {"name": "Alpha Game", "year": "1995"}
        ]
        
        result = sort_games(games, "name")
        assert result[0]["name"] == "Alpha Game"
        assert result[1]["name"] == "Zebra Game"

    def test_sort_by_year_ascending(self):
        """Test sorting by year in ascending order."""
        games = [
            {"name": "New Game", "year": "1995"},
            {"name": "Old Game", "year": "1990"},
            {"name": "No Year Game", "year": None}
        ]
        
        result = sort_games(games, "year")
        assert result[0]["name"] == "No Year Game"  # None becomes 0
        assert result[1]["name"] == "Old Game"
        assert result[2]["name"] == "New Game"

    def test_sort_invalid_field(self):
        """Test sorting with invalid field falls back to name."""
        games = [
            {"name": "Zebra Game", "year": "1990"},
            {"name": "Alpha Game", "year": "1995"}
        ]
        
        result = sort_games(games, "invalid_field")
        assert result[0]["name"] == "Alpha Game"
        assert result[1]["name"] == "Zebra Game"


class TestDisplayGames:
    """Test the display_games function."""
    
    def test_display_games_with_year(self):
        """Test displaying games that have years."""
        games = [
            {"id": "abc123", "name": "Test Game", "year": "1990"},
            {"id": "def456", "name": "Another Game", "year": "1995"}
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            display_games(games)
            output = mock_stdout.getvalue()
            
            assert "abc123" in output
            assert "Test Game" in output
            assert "1990" in output
            assert "def456" in output
            assert "Another Game" in output  
            assert "1995" in output

    def test_display_games_without_year(self):
        """Test displaying games without years."""
        games = [
            {"id": "abc123", "name": "Test Game", "year": None}
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            display_games(games)
            output = mock_stdout.getvalue()
            
            assert "abc123" in output
            assert "Test Game" in output
            # Should show None when year is None (since get() returns None)
            assert "(None)" in output

    def test_display_games_missing_year_key(self):
        """Test displaying games with missing year key."""
        games = [
            {"id": "abc123", "name": "Test Game"}  # No year key
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            display_games(games)
            output = mock_stdout.getvalue()
            
            assert "abc123" in output
            assert "Test Game" in output
            # Should show ---- when year key is missing
            assert "(----)" in output

    def test_display_empty_games_list(self):
        """Test displaying empty games list."""
        games = []
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            display_games(games)
            output = mock_stdout.getvalue()
            
            # Should not crash and produce minimal output
            assert output.strip() == ""

    def test_display_games_truncates_long_ids(self):
        """Test that long IDs are properly displayed."""
        games = [
            {"id": "verylongidstring", "name": "Test Game", "year": "1990"}
        ]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            display_games(games)
            output = mock_stdout.getvalue()
            
            # Should show the full ID as provided
            assert "verylongidstring" in output
