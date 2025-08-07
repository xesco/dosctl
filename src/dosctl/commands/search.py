import click
import re
from dosctl.lib.decorators import ensure_cache
from dosctl.lib.display import sort_games, display_games

@click.command()
@click.argument('query', required=False)
@click.option('-c', '--case-sensitive', is_flag=True, default=False, help='Perform a case-sensitive search.')
@click.option('-y', '--year', type=int, help='Filter search results by a specific year.')
@click.option('-s', '--sort-by', type=click.Choice(['name', 'year'], case_sensitive=False), default='name', help='Sort the results by name or year.')
@ensure_cache
def search(collection, query, case_sensitive, year, sort_by):
    """
    Searches for games in the local cache.
    """
    if not query and not year:
        click.echo("Error: You must provide a search query or a year.", err=True)
        return

    games = collection.get_games()

    if not games:
        click.echo("No games found in cache.")
        return

    # Search Logic
    results = []
    flags = 0 if case_sensitive else re.IGNORECASE

    for game in games:
        # Year filter
        if year and str(game.get('year')) != str(year):
            continue

        # Name filter (only if query is provided)
        if query and not re.search(query, game['name'], flags):
            continue

        results.append(game)

    # Display Logic
    if not results:
        click.echo("No games found matching your criteria.")
        return

    results = sort_games(results, sort_by)
    display_games(results, f"Found {len(results)} game(s):")
