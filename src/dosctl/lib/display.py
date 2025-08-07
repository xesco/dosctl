"""Utility functions for displaying game information."""
import click

def sort_games(games, sort_by='name'):
    """Sort games by name or year."""
    if sort_by == 'year':
        return sorted(games, key=lambda g: int(g.get('year', 0) or 0))
    else:
        return sorted(games, key=lambda g: g['name'])

def display_games(games, title="Available Games:"):
    """Display a list of games in a consistent format."""
    if not games:
        return

    click.echo(title)
    for game in games:
        year_str = f"({game.get('year', '----')})"
        click.echo(f"  [{game['id']}] {year_str} {game['name']}")
