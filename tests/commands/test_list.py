from unittest.mock import patch
from click.testing import CliRunner
from dosctl.main import cli

@patch('dosctl.lib.decorators.create_collection')
def test_list_command_runs(mock_create_collection):
    """A basic smoke test to ensure the list command runs."""
    runner = CliRunner()
    mock_collection_instance = mock_create_collection.return_value
    mock_collection_instance.get_games.return_value = []
    
    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert "No games found" in result.output
