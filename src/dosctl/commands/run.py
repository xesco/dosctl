import click
import subprocess
import textwrap
from dosctl.lib.decorators import ensure_cache
from dosctl.lib.game import install_game
from dosctl.lib.config_store import get_game_command, set_game_command
from dosctl.lib.system import is_dosbox_installed
from dosctl.lib.executables import find_executables, executable_exists
from dosctl.lib.dosbox import get_dosbox_launcher

@click.command()
@click.argument('game_id')
@click.argument('command_parts', nargs=-1)
@click.option('-c', '--configure', is_flag=True, default=False, help='Force re-selection of the default executable.')
@ensure_cache
def run(collection, game_id, command_parts, configure):
    """
    Runs a game. Prompts for an executable on the first run or when --configure is used.
    """
    if not is_dosbox_installed():
        help_text = textwrap.dedent("""
            Error: 'dosbox' command not found in your PATH.

            Please install DOSBox. We recommend DOSBox Staging for the best experience.

            To install with Homebrew on macOS:
              brew install dosbox           # For standard DOSBox
              brew install dosbox-staging # For DOSBox Staging (recommended)

            If you install DOSBox Staging, you may need to create a symlink so `dosctl` can find it:
              ln -s "$(brew --prefix dosbox-staging)/bin/dosbox-staging" ~/.local/bin/dosbox
        """)
        click.echo(help_text, err=True)
        return

    try:
        _, game_install_path = install_game(collection, game_id)
        if not game_install_path:
            return

        # Determine the command to run
        chosen_command_str = _get_or_prompt_command(game_id, game_install_path, command_parts, configure)
        if not chosen_command_str:
            return

        # Save the chosen command for future runs
        set_game_command(game_id, chosen_command_str)

        # Validate that the chosen executable exists
        executable_name = chosen_command_str.split()[0]
        if not executable_exists(game_install_path, executable_name):
            click.echo(f"Error: Executable '{executable_name}' not found.", err=True)
            set_game_command(game_id, None)
            return

        # Launch the game
        _launch_game(game_install_path, chosen_command_str)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)

def _get_or_prompt_command(game_id, game_install_path, command_parts, configure):
    """Get the command to run, prompting if necessary."""
    if configure:
        return _prompt_for_executable(game_install_path, configure)

    # If user provides command on CLI, use it
    if command_parts:
        return " ".join(command_parts)

    # Check for saved command
    saved_command = get_game_command(game_id)
    if saved_command:
        return saved_command

    # First run - prompt for executable
    click.echo(f"No default executable set for game '{game_id}'. Searching...")
    return _prompt_for_executable(game_install_path, configure)

def _prompt_for_executable(game_install_path, force_menu=False):
    """Prompt user to select an executable."""
    executables = find_executables(game_install_path)

    if not executables:
        click.echo(f"Error: No executables (.exe, .com, .bat) found in the archive.", err=True)
        return None

    # If there's only one option and we're not forcing the menu, choose it automatically
    if len(executables) == 1 and not force_menu:
        click.echo(f"Found a single executable: '{executables[0]}'. Setting as default.")
        return executables[0]

    # Show menu for user selection
    while True:
        menu_items = [f"  {i}: {exe_name.upper()}" for i, exe_name in enumerate(executables, 1)]
        click.echo("Please choose one of the following to run:")
        click.echo("\n".join(menu_items))

        choice = click.prompt("Select a file to execute", type=int)
        if 1 <= choice <= len(executables):
            return executables[choice - 1]
        else:
            click.echo("Invalid choice. Please try again.", err=True)

def _launch_game(game_install_path, chosen_command_str):
    """Launch the game with DOSBox."""
    click.echo(f"Starting '{chosen_command_str.upper()}' with DOSBox...")

    try:
        # Use the new DOSBox abstraction layer
        launcher = get_dosbox_launcher()
        launcher.launch_game(
            game_path=game_install_path,
            command=chosen_command_str,
            exit_on_completion=True  # This matches the previous -c exit behavior
        )
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo("Please ensure DOSBox is installed and available in your system PATH.", err=True)
    except Exception as e:
        click.echo(f"Error launching game: {e}", err=True)
