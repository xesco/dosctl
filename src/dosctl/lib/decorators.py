from functools import wraps

from dosctl.collections.factory import create_collection
from dosctl.config import (
    COLLECTION_CACHE_DIR,
    DEFAULT_COLLECTION_SOURCE,
    DEFAULT_COLLECTION_TYPE,
    ensure_dirs_exist,
)


def ensure_cache(f):
    """
    A decorator that ensures the game cache is present and provides the
    collection object to the command.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ensure_dirs_exist()
        collection = create_collection(
            DEFAULT_COLLECTION_TYPE,
            source=DEFAULT_COLLECTION_SOURCE,
            cache_dir=COLLECTION_CACHE_DIR,
        )
        # This will auto-refresh if the cache is missing
        collection.ensure_cache_is_present()

        # Pass the collection object to the command
        return f(collection, *args, **kwargs)
    return decorated_function
