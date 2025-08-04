import click
import subprocess
import textwrap
from dosctl.lib.decorators import ensure_cache
from dosctl.lib.game import install_game
from dosctl.lib.config_store import get_game_command, set_game_command
from dosctl.lib.system import is_dosbox_installed

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
        game, game_install_path = install_game(collection, game_id)
        if not game_install_path:
            return

        # Step 1: Determine the command to run.
        # If the user provides a command on the CLI, it takes highest priority.
        # Otherwise, we check the config store for a saved command.
        chosen_command_str = " ".join(command_parts) if command_parts else get_game_command(game_id)

        # Step 2: If no command is found (first run), prompt the user.
        if not chosen_command_str:
            click.echo(f"No default executable set for game '{game_id}'. Searching...")
            
            executables = list(game_install_path.glob('**/*.[eE][xX][eE]'))
            executables.extend(list(game_install_path.glob('**/*.[cC][oO][mM]')))
            executables.extend(list(game_install_path.glob('**/*.[bB][aA][tT]')))
            
            if not executables:
                click.echo(f"Error: No executables (.exe, .com, .bat) found in the archive for game '{game_id}'.", err=True)
                return
            
            sorted_executables = sorted([e.name for e in executables])

            # If there's only one option, choose it automatically.
            if len(sorted_executables) == 1 and not configure:
                chosen_command_str = sorted_executables[0]
                click.echo(f"Found a single executable: '{chosen_command_str}'. Setting as default.")
            else:
                # Loop until the user makes a valid choice
                while True:
                    menu_items = [f"  {i}: {exe_name.upper()}" for i, exe_name in enumerate(sorted_executables, 1)]
                    menu_text = "\n".join(menu_items)
                    click.echo("Please choose one of the following to run:")
                    click.echo(menu_text)
                    
                    choice = click.prompt("Select a file to execute", type=int, default=1)
                    if 1 <= choice <= len(sorted_executables):
                        chosen_command_str = sorted_executables[choice - 1]
                        break # Exit the loop on valid choice
                    else:
                        click.echo("Invalid choice. Please try again.", err=True)

        # Step 3: Save the chosen command for future runs.
        set_game_command(game_id, chosen_command_str)
        
        # Step 4: Validate that the chosen executable exists.
        executable_name = chosen_command_str.split()[0]
        game_exe_path = game_install_path / executable_name
        if not game_exe_path.exists():
            click.echo(f"Error: Executable '{executable_name}' not found.", err=True)
            set_game_command(game_id, None)
            return

        # Step 5: Launch the game.
        click.echo(f"Starting '{chosen_command_str.upper()}' with DOSBox...")
        
        command = [
            'dosbox',
            '-c', f'MOUNT C "{game_install_path}"',
            '-c', 'C:',
            '-c', chosen_command_str
        ]
        
        subprocess.Popen(command,
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
    except Exception as e:
        click.echo(f"An unexpected error occurred: {e}", err=True)
