import click
from dosctl.collections.archive_org import ArchiveOrgCollection
from dosctl.config import DEFAULT_COLLECTION_SOURCE, COLLECTION_CACHE_DIR

@click.command(name="list")
def list_games():
    """Lists all available games from the local cache."""
    collection = ArchiveOrgCollection(
        source=DEFAULT_COLLECTION_SOURCE,
        cache_dir=COLLECTION_CACHE_DIR
    )
    
    games = collection.get_games()
    
    if not games:
        click.echo("No games found in the cache. Have you run 'dosctl refresh' yet?")
        return
        
    click.echo("Available Games:")
    for game in games:
        click.echo(f"  [{game['id']}] {game['name']}")
