import click
from pathlib import Path
from dosctl.config import DATA_DIR
from dosctl.lib.decorators import ensure_cache

@click.command()
@click.argument('game_id')
@ensure_cache
def inspect(collection, game_id):
    """
    Inspects the installed files for a given game.
    """
    install_dir = DATA_DIR / 'installed'
    game_install_path = install_dir / game_id

    if not game_install_path.exists() or not game_install_path.is_dir():
        click.echo(f"Error: Game with ID '{game_id}' is not installed.", err=True)
        return

    game = collection._find_game(game_id)
    game_name = game['name'] if game else "Unknown Game"

    click.echo(f"Inspecting files for '{game_name}' (ID: {game_id})")
    click.echo(f"Location: {game_install_path}")
    click.echo("-" * 40)

    # Use rglob to list all files recursively
    files = sorted([f for f in game_install_path.rglob('*') if f.is_file()])

    if not files:
        click.echo("No files found in the installation directory.")
        return

    for file_path in files:
        # Get the path relative to the game's install directory
        relative_path = file_path.relative_to(game_install_path)
        click.echo(f"  {relative_path}")
