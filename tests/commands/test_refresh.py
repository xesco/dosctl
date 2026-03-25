"""Tests for the refresh command."""
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from dosctl.main import cli


class TestRefreshCommand:
    def test_without_force_shows_instructions_and_does_not_refresh(self):
        runner = CliRunner()
        with patch("dosctl.commands.refresh.create_collection") as mock_col:
            result = runner.invoke(cli, ["refresh"])
        assert "--force" in result.output
        mock_col.assert_not_called()

    def test_with_force_creates_dirs_and_refreshes_cache(self):
        runner = CliRunner()
        mock_collection = MagicMock()
        with patch("dosctl.commands.refresh.create_collection", return_value=mock_collection), \
             patch("dosctl.commands.refresh.ensure_dirs_exist") as mock_dirs:
            result = runner.invoke(cli, ["refresh", "--force"])
        assert result.exit_code == 0
        mock_dirs.assert_called_once()
        mock_collection.ensure_cache_is_present.assert_called_once_with(force_refresh=True)
