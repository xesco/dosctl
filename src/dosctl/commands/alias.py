"""Alias management commands."""

import click
from dosctl.lib.aliases import set_alias, remove_alias, list_aliases, _validate_alias
from dosctl.lib.decorators import ensure_cache


@click.group()
def alias():
    """Manage aliases for game IDs.

    Aliases let you refer to a game by a memorable name instead of its
    8-character ID:

      dosctl alias set doom 62ef2769

      dosctl play doom
    """


@alias.command(name="set")
@click.argument("alias_name")
@click.argument("game_id")
@ensure_cache
def alias_set(collection, alias_name, game_id):
    """Create or update ALIAS_NAME pointing to GAME_ID."""
    try:
        _validate_alias(alias_name)
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        return

    game = collection.find_game(game_id)
    if not game:
        click.echo(f"Error: No game with ID '{game_id}' found in the collection.", err=True)
        return

    set_alias(alias_name, game_id, game["name"])
    click.echo(f"Alias '{alias_name}' → '{game_id}' ({game['name']}) saved.")


@alias.command(name="remove")
@click.argument("alias_name")
def alias_remove(alias_name):
    """Remove ALIAS_NAME."""
    try:
        remove_alias(alias_name)
        click.echo(f"Alias '{alias_name}' removed.")
    except KeyError:
        click.echo(f"Error: No alias '{alias_name}' found.", err=True)


@alias.command(name="list")
def alias_list():
    """List all defined aliases."""
    aliases = list_aliases()
    if not aliases:
        click.echo("No aliases defined. Use 'dosctl alias set' to create one.")
        return
    click.echo("Defined aliases:")
    for name, entry in sorted(aliases.items()):
        click.echo(f"  {name} → {entry['id']} ({entry['name']})")
