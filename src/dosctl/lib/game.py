from pathlib import Path
import click
from .decorators import ensure_cache

def install_game(collection, game_id):
    """
    Ensures a game is installed, downloading and unzipping it if necessary.
    Returns the game object and the installation path.
    """
    # Step 1: Define standard paths for downloads and installations
    download_dir = Path.home() / ".local" / "share" / "dosctl" / "downloads"
    install_dir = Path.home() / ".local" / "share" / "dosctl" / "installed"
    
    # Step 2: Find the game in the collection
    game = collection._find_game(game_id)
    if not game:
        raise FileNotFoundError(f"Game with ID '{game_id}' not found.")

    game_install_path = install_dir / game_id
    
    # Step 3: If the game is already installed, we're done.
    if game_install_path.exists():
        click.echo(f"'{game['name']}' is already installed.")
        return game, game_install_path

    # Step 4: Download the game if it's not already cached
    download_path = collection.download_game(game_id, str(download_dir))
    if not download_path:
        # The download method will print an error, so we just exit.
        return None, None
    
    # Step 5: Unzip the game to its final installation directory
    collection.unzip_game(game_id, download_dir, game_install_path)
    
    click.echo(f"✅ Successfully installed '{game['name']}'")
    return game, game_install_path
