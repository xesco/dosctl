import click
from dosctl.config import INSTALLED_DIR
from dosctl.lib.decorators import ensure_cache

@click.command()
@click.argument('game_id')
@click.option('-e', '--executables', is_flag=True, help='Show only executable files (.exe, .com, .bat).')
@ensure_cache
def inspect(collection, game_id, executables):
    """
    Inspects the installed files for a given game.
    """
    game_install_path = INSTALLED_DIR / game_id

    if not game_install_path.exists() or not game_install_path.is_dir():
        click.echo(f"Error: Game with ID '{game_id}' is not installed.", err=True)
        return

    game = collection.find_game(game_id)
    game_name = game['name'] if game else "Unknown Game"

    click.echo(f"Inspecting files for '{game_name}' (ID: {game_id})")
    click.echo(f"Location: {game_install_path}")
    click.echo("-" * 40)

    # Use rglob to list all files recursively
    files = sorted([f for f in game_install_path.rglob('*') if f.is_file()])

    if executables:
        # Filter to only executable file extensions
        executable_extensions = {'.exe', '.com', '.bat'}
        files = [f for f in files if f.suffix.lower() in executable_extensions]

    if not files:
        if executables:
            click.echo("No executable files found in the installation directory.")
        else:
            click.echo("No files found in the installation directory.")
        return

    if executables:
        click.echo("Executable files:")

    for file_path in files:
        # Get the path relative to the game's install directory
        relative_path = file_path.relative_to(game_install_path)
        click.echo(f"  {relative_path}")
