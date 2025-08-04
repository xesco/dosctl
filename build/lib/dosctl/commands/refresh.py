import click
from dosctl.collections.archive_org import ArchiveOrgCollection
from dosctl.config import DEFAULT_COLLECTION_SOURCE, COLLECTION_CACHE_DIR, ensure_dirs_exist

@click.command()
def refresh():
    """
    Fetches the latest game lists from the collection source and updates the
    local cache.
    """
    click.echo("Ensuring application directories exist...")
    ensure_dirs_exist()
    
    click.echo("Initializing collection...")
    collection = ArchiveOrgCollection(
        source=DEFAULT_COLLECTION_SOURCE,
        cache_dir=COLLECTION_CACHE_DIR
    )
    
    click.echo("Refreshing game lists. This may take a moment...")
    collection.load(force_refresh=True)
    
    click.echo("✅ Game lists refreshed successfully.")
