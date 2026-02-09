from pathlib import Path
import click
from dosctl.config import DOWNLOADS_DIR, INSTALLED_DIR

def install_game(collection, game_id):
    """
    Ensures a game is installed, downloading and unzipping it if necessary.
    Returns the game object and the installation path.
    """
    # Find the game in the collection
    game = collection.find_game(game_id)
    if not game:
        raise FileNotFoundError(f"Game with ID '{game_id}' not found.")

    game_install_path = INSTALLED_DIR / game_id

    # If the game is already installed, we're done.
    if game_install_path.exists():
        click.echo(f"'{game['name']}' is already installed.")
        return game, game_install_path

    # Download the game if it's not already cached
    download_path = collection.download_game(game_id, str(DOWNLOADS_DIR))
    if not download_path:
        # The download method will print an error, so we just exit.
        return None, None

    # Unzip the game to its final installation directory
    collection.unzip_game(game_id, DOWNLOADS_DIR, game_install_path)
    
    click.echo(f"✅ Successfully installed '{game['name']}'")
    return game, game_install_path
