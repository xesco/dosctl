import click

from dosctl.collections.factory import create_collection
from dosctl.config import ensure_dirs_exist
from dosctl.lib.collections_store import resolve_collection


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

    resolved = resolve_collection()
    collection = create_collection(
        resolved.type,
        source=resolved.source,
        cache_dir=resolved.cache_dir,
    )

    click.echo("Rebuilding the catalog...")
    collection.ensure_cache_is_present(force_refresh=True)
