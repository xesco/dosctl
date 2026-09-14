import click

from dosctl.collections.factory import create_collection
from dosctl.config import (
    COLLECTION_CACHE_DIR,
    DEFAULT_COLLECTION_SOURCE,
    DEFAULT_COLLECTION_TYPE,
    ensure_dirs_exist,
)


@click.command()
@click.option('--force', is_flag=True, default=False, help='Rebuild the catalog without the reminder.')
def refresh(force):
    """
    Rebuilds the catalog from the collection source.
    """
    if not force:
        click.echo("This command will rebuild the entire catalog.")
        click.echo("Use 'dosctl refresh --force' to confirm.")
        return

    click.echo("Ensuring application directories exist...")
    ensure_dirs_exist()

    collection = create_collection(
        DEFAULT_COLLECTION_TYPE,
        source=DEFAULT_COLLECTION_SOURCE,
        cache_dir=COLLECTION_CACHE_DIR,
    )

    click.echo("Rebuilding the catalog...")
    collection.ensure_cache_is_present(force_refresh=True)
