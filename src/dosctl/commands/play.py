import click
import textwrap
from dosctl.lib.decorators import ensure_cache
from dosctl.lib.game import install_game
from dosctl.lib.config_store import set_game_command
from dosctl.lib.executables import executable_exists, get_or_prompt_command
from dosctl.lib.dosbox import is_dosbox_installed, get_dosbox_launcher


@click.command()
@click.argument("game_id")
@click.argument("command_parts", nargs=-1)
@click.option(
    "-c",
    "--configure",
    is_flag=True,
    default=False,
    help="Force re-selection of the default executable.",
)
@click.option(
    "-a",
    "--floppy",
    is_flag=True,
    default=False,
    help="Also mount game directory as A: drive and start there. Useful for floppy-based installers.",
)
@click.option(
    "-n",
    "--no-exec",
    is_flag=True,
    default=False,
    help="Open DOSBox with the game directory mounted but don't run anything. Useful for debugging.",
)
@ensure_cache
def play(collection, game_id, command_parts, configure, floppy, no_exec):
    """
    Plays a game. Prompts for an executable on the first run or when --configure is used.
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
        # --no-exec is incompatible with command_parts and --configure
        if no_exec and (command_parts or configure):
            click.echo(
                "Error: --no-exec cannot be used with --configure or command arguments.",
                err=True,
            )
            return

        _, game_install_path = install_game(collection, game_id)
        if not game_install_path:
            return

        # No-exec mode: just mount the game directory and drop to DOS prompt
        if no_exec:
            _launch_game(game_install_path, floppy=floppy)
            return

        # Determine the command to run
        chosen_command_str = get_or_prompt_command(
            game_id, game_install_path, command_parts, configure
        )
        if not chosen_command_str:
            return

        if floppy:
            # Floppy mode: skip saving default and executable validation
            # (the command may reference floppy paths or drive letters)
            _launch_game(game_install_path, chosen_command_str, floppy=True)
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


def _launch_game(game_install_path, chosen_command_str=None, floppy=False):
    """Launch the game with DOSBox.

    If chosen_command_str is None, opens DOSBox at the mounted directory
    without running any executable.
    """
    if chosen_command_str:
        click.echo(f"Starting '{chosen_command_str.upper()}' with DOSBox...")
    else:
        click.echo("Opening DOSBox at game directory...")

    try:
        # Use the new DOSBox abstraction layer
        launcher = get_dosbox_launcher()
        launcher.launch_game(
            game_path=game_install_path,
            command=chosen_command_str,
            exit_on_completion=True,
            floppy=floppy,
        )
    except RuntimeError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            "Please ensure DOSBox is installed and available in your system PATH.",
            err=True,
        )
    except Exception as e:
        click.echo(f"Error launching game: {e}", err=True)
