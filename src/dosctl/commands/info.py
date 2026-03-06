"""Info command — show catalog metadata and local status for a game."""
import click
from dosctl.config import DOWNLOADS_DIR, INSTALLED_DIR
from dosctl.lib.decorators import ensure_cache
from dosctl.lib.aliases import resolve_game_id, list_aliases
from dosctl.lib.config_store import get_game_command


@click.command()
@click.argument("game_id", metavar="GAME_ID|ALIAS")
@ensure_cache
def info(collection, game_id):
    """Show information about a game."""
    game_id = resolve_game_id(game_id)

    game = collection.find_game(game_id)
    if not game:
        click.echo(f"Error: No game with ID '{game_id}' found in the collection.", err=True)
        return

    # Resolve alias (invert the alias map to find any alias for this game)
    alias = next(
        (name for name, entry in list_aliases().items() if entry["id"] == game_id),
        None,
    )

    # Determine status and relevant paths
    install_path = INSTALLED_DIR / game_id
    archive_path = DOWNLOADS_DIR / f"{game['name']}.zip"

    if install_path.exists():
        status = "Installed"
    elif archive_path.exists():
        status = "Downloaded"
    else:
        status = "Not downloaded"

    # Saved default executable
    command = get_game_command(game_id)

    # Display
    click.echo(f"Name:    {game['name']}")
    click.echo(f"ID:      {game_id}")
    click.echo(f"Year:    {game.get('year') or '----'}")
    if alias:
        click.echo(f"Alias:   {alias}")
    click.echo(f"Status:  {status}")
    if status == "Downloaded":
        click.echo(f"Archive: {archive_path}")
    if status == "Installed":
        click.echo(f"Path:    {install_path}")
    if command:
        click.echo(f"Command: {command}")
