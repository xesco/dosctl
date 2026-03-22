import click
import shutil
from dosctl.config import INSTALLED_DIR, DOWNLOADS_DIR
from dosctl.lib.decorators import ensure_cache
from dosctl.lib.aliases import resolve_game_id, remove_aliases_for_game_id
from dosctl.lib.config_store import get_game_command, set_game_command


@click.command()
@click.argument("game_id", metavar="GAME_ID|ALIAS")
@ensure_cache
def delete(collection, game_id):
    """
    Deletes an installed game.
    """
    game_id = resolve_game_id(game_id)
    game_install_path = INSTALLED_DIR / game_id

    if not game_install_path.exists() or not game_install_path.is_dir():
        click.echo(f"Error: Game with ID '{game_id}' is not installed.", err=True)
        return

    game = collection.find_game(game_id)
    game_name = game["name"] if game else f"Game ID {game_id}"
    downloaded_zip = DOWNLOADS_DIR / f"{game_name}.zip"
    saved_command = get_game_command(game_id)

    click.echo(f"You are about to delete the files for '{game_name}'.")
    click.echo(f"Installation: {game_install_path}")
    if downloaded_zip.exists():
        click.echo(f"Downloaded Archive: {downloaded_zip}")

    if not click.confirm("Are you sure you want to continue?"):
        click.echo("Deletion cancelled.")
        return

    try:
        if game_install_path.exists():
            shutil.rmtree(game_install_path)
            click.echo(f"✅ Successfully deleted installation directory.")

        if downloaded_zip.exists():
            downloaded_zip.unlink()
            click.echo(f"✅ Successfully deleted downloaded archive.")

        removed_aliases = remove_aliases_for_game_id(game_id)
        if removed_aliases:
            click.echo(f"✅ Removed aliases: {', '.join(removed_aliases)}")

        if saved_command is not None:
            set_game_command(game_id, None)
            click.echo("✅ Removed saved launch command.")

    except Exception as e:
        click.echo(f"An error occurred during deletion: {e}", err=True)
