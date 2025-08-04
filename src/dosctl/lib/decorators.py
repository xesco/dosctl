from functools import wraps
import click
from dosctl.collections.archive_org import ArchiveOrgCollection
from dosctl.config import DEFAULT_COLLECTION_SOURCE, COLLECTION_CACHE_DIR, ensure_dirs_exist

def ensure_cache(f):
    """
    A decorator that ensures the game cache is present and provides the
    collection object to the command.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ensure_dirs_exist()
        collection = ArchiveOrgCollection(
            source=DEFAULT_COLLECTION_SOURCE,
            cache_dir=COLLECTION_CACHE_DIR
        )
        # This will auto-refresh if the cache is missing
        collection.ensure_cache_is_present()
        
        # Pass the collection object to the command
        return f(collection, *args, **kwargs)
    return decorated_function
