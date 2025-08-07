from unittest.mock import patch
from click.testing import CliRunner
from dosctl.main import cli

@patch('dosctl.lib.decorators.TotalDOSCollectionRelease14')
def test_list_command_runs(mock_collection_class):
    """A basic smoke test to ensure the list command runs."""
    runner = CliRunner()
    mock_collection_instance = mock_collection_class.return_value
    mock_collection_instance.get_games.return_value = []
    
    result = runner.invoke(cli, ['list'])
    assert result.exit_code == 0
    assert "No games found" in result.output
