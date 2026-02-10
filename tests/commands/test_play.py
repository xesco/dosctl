from unittest.mock import patch
from click.testing import CliRunner
from dosctl.main import cli

@patch('dosctl.commands.play.is_dosbox_installed', return_value=True)
@patch('dosctl.commands.play.install_game')
def test_play_command_game_not_found(mock_install_game, mock_is_installed):
    """Tests that the play command handles a missing game."""
    runner = CliRunner()
    mock_install_game.side_effect = FileNotFoundError("Game not found")

    result = runner.invoke(cli, ['play', 'fake_id'])
    assert result.exit_code == 0
    assert "Error: Game not found" in result.output
