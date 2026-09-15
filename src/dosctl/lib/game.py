import shutil

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

    # Each collection installs into its own subdirectory when scoped, so that
    # two collections cannot collide on the same game ID.
    game_install_path = resolve_install_path(collection, game_id)

    # If the game is already installed, we're done.
    if game_install_path.exists():
        click.echo(f"'{game['name']}' is already installed.")
        return game, game_install_path

    # Download the game if it's not already cached
    downloads_dir = collection.downloads_dir_for(DOWNLOADS_DIR)
    download_path = collection.download_game(game_id, str(downloads_dir))
    if not download_path:
        # The download method will print an error, so we just exit.
        return None, None

    # Unzip the game to its final installation directory
    collection.unzip_game(game_id, downloads_dir, game_install_path)

    click.echo(f"✅ Successfully installed '{game['name']}'")
    return game, game_install_path


def resolve_install_path(collection, game_id):
    """
    The install directory for the game under the collection's scope, moving a
    legacy flat-layout installation into the scope on first sight.
    """
    scoped_path = collection.installed_dir_for(INSTALLED_DIR) / game_id
    if collection.scope:
        legacy_path = INSTALLED_DIR / game_id
        if not scoped_path.exists() and legacy_path.exists() and legacy_path.is_dir():
            scoped_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(legacy_path), str(scoped_path))
            click.echo(f"Moved '{game_id}' into '{scoped_path.parent}'.")
    return scoped_path
