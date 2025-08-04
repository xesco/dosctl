import click
from pathlib import Path
from dosctl.lib.decorators import ensure_cache
from dosctl.config import DATA_DIR

@click.command(name="list")
@click.option('-s', '--sort-by', type=click.Choice(['name', 'year'], case_sensitive=False), default='name', help='Sort the list by name or year.')
@click.option('-i', '--installed', is_flag=True, default=False, help='Only list installed games.')
@ensure_cache
def list_games(collection, sort_by, installed):
    """Lists all available games from the local cache."""
    
    games = collection.get_games()
    
    if installed:
        install_dir = DATA_DIR / 'installed'
        installed_ids = {p.name for p in install_dir.iterdir() if p.is_dir()}
        games = [g for g in games if g['id'] in installed_ids]

    if not games:
        if installed:
            click.echo("No games are currently installed.")
        else:
            click.echo("No games found in cache.")
        return
        
    # Sort the games based on the user's choice
    if sort_by == 'year':
        games = sorted(games, key=lambda g: int(g.get('year', 0) or 0))
    else:
        games = sorted(games, key=lambda g: g['name'])

    click.echo("Available Games:")
    for game in games:
        year_str = f"({game.get('year', '----')})"
        click.echo(f"  [{game['id']}] {year_str} {game['name']}")
