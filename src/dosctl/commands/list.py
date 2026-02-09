import click
from dosctl.lib.decorators import ensure_cache
from dosctl.lib.display import sort_games, display_games
from dosctl.config import INSTALLED_DIR

@click.command(name="list")
@click.option('-s', '--sort-by', type=click.Choice(['name', 'year'], case_sensitive=False), default='name', help='Sort the list by name or year.')
@click.option('-i', '--installed', is_flag=True, default=False, help='Only list installed games.')
@ensure_cache
def list_games(collection, sort_by, installed):
    """Lists all available games from the local cache."""
    
    games = collection.get_games()

    if installed:
        installed_ids = {p.name for p in INSTALLED_DIR.iterdir() if p.is_dir()} if INSTALLED_DIR.exists() else set()
        games = [g for g in games if g['id'] in installed_ids]

    if not games:
        message = "No games are currently installed." if installed else "No games found in cache."
        click.echo(message)
        return

    games = sort_games(games, sort_by)
    display_games(games)
