import click
from dosctl.collections.archive_org import ArchiveOrgCollection
from dosctl.config import DEFAULT_COLLECTION_SOURCE, COLLECTION_CACHE_DIR, ensure_dirs_exist

@click.command()
@click.option('--force', is_flag=True, default=False, help='Force a re-download of the game list.')
def refresh(force):
    """
    Downloads the latest game list from the collection source.
    """
    if not force:
        click.echo("This command will re-download the entire game list.")
        click.echo("Use 'dosctl refresh --force' to confirm.")
        return

    click.echo("Ensuring application directories exist...")
    ensure_dirs_exist()
    
    collection = ArchiveOrgCollection(
        source=DEFAULT_COLLECTION_SOURCE,
        cache_dir=COLLECTION_CACHE_DIR
    )
    
    click.echo("Forcing a refresh of the game lists...")
    collection.ensure_cache_is_present(force_refresh=True)
