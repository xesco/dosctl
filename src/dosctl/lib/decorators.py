from functools import wraps

from dosctl.collections.factory import create_collection
from dosctl.config import ensure_dirs_exist
from dosctl.lib.collections_store import resolve_collection


def ensure_cache(f):
    """
    A decorator that ensures the game cache is present and provides the
    collection object to the command.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ensure_dirs_exist()
        resolved = resolve_collection()
        collection = create_collection(
            resolved.type,
            source=resolved.source,
            cache_dir=resolved.cache_dir,
        )
        # This will auto-refresh if the cache is missing
        collection.ensure_cache_is_present()

        # Pass the collection object to the command
        return f(collection, *args, **kwargs)
    return decorated_function
