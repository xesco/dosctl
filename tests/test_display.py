"""Tests for the display utilities."""
from unittest.mock import patch
from io import StringIO

from dosctl.lib.display import sort_games, display_games


class TestSortGames:
    def test_sort_by_name_ascending(self):
        games = [{"name": "Zebra Game", "year": "1990"}, {"name": "Alpha Game", "year": "1995"}]
        result = sort_games(games, "name")
        assert result[0]["name"] == "Alpha Game"
        assert result[1]["name"] == "Zebra Game"

    def test_sort_by_year_ascending(self):
        games = [
            {"name": "New Game", "year": "1995"},
            {"name": "Old Game", "year": "1990"},
            {"name": "No Year Game", "year": None},
        ]
        result = sort_games(games, "year")
        assert result[0]["name"] == "No Year Game"
        assert result[1]["name"] == "Old Game"
        assert result[2]["name"] == "New Game"

    def test_sort_invalid_field_falls_back_to_name(self):
        games = [{"name": "Zebra Game", "year": "1990"}, {"name": "Alpha Game", "year": "1995"}]
        result = sort_games(games, "invalid_field")
        assert result[0]["name"] == "Alpha Game"


class TestDisplayGames:
    def test_display_games_with_year(self):
        games = [{"id": "abc123", "name": "Test Game", "year": "1990"}]
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            display_games(games)
            output = mock_stdout.getvalue()
        assert "abc123" in output
        assert "Test Game" in output
        assert "1990" in output

    def test_display_games_without_year(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            display_games([{"id": "abc123", "name": "Test Game", "year": None}])
            output = mock_stdout.getvalue()
        assert "(None)" in output

    def test_display_games_missing_year_key(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            display_games([{"id": "abc123", "name": "Test Game"}])
            output = mock_stdout.getvalue()
        assert "(----)" in output

    def test_display_empty_games_list(self):
        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            display_games([])
            assert mock_stdout.getvalue().strip() == ""
