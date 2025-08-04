import click
import shutil
from dosctl.config import DATA_DIR
from dosctl.lib.decorators import ensure_cache

@click.command()
@click.argument('game_id')
@ensure_cache
def delete(collection, game_id):
    """
    Deletes an installed game.
    """
    install_dir = DATA_DIR / 'installed'
    game_install_path = install_dir / game_id

    if not game_install_path.exists() or not game_install_path.is_dir():
        click.echo(f"Error: Game with ID '{game_id}' is not installed.", err=True)
        return

    game = collection._find_game(game_id)
    download_dir = DATA_DIR / 'downloads'
    game_name = game['name'] if game else f"Game ID {game_id}"
    downloaded_zip = download_dir / f"{game_name}.zip"

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

    except Exception as e:
        click.echo(f"An error occurred during deletion: {e}", err=True)
