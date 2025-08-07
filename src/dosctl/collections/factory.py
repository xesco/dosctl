"""Collection factory for creating appropriate collection instances."""
from .archive_org import TotalDOSCollectionRelease14

# Registry of available collection implementations
COLLECTION_REGISTRY = {
    "tdc_release_14": TotalDOSCollectionRelease14,
    # Future versions can be added here:
    # "tdc_release_15": TotalDOSCollectionRelease15,
}

def create_collection(collection_type: str, source: str, cache_dir: str):
    """
    Factory function to create collection instances.
    
    Args:
        collection_type: The type of collection (e.g., "tdc_release_14")
        source: The source URL for the collection
        cache_dir: Directory for caching collection data
        
    Returns:
        An instance of the appropriate collection class
        
    Raises:
        ValueError: If the collection_type is not supported
    """
    if collection_type not in COLLECTION_REGISTRY:
        available = ", ".join(COLLECTION_REGISTRY.keys())
        raise ValueError(f"Unknown collection type '{collection_type}'. Available: {available}")
    
    collection_class = COLLECTION_REGISTRY[collection_type]
    return collection_class(source, cache_dir)

def get_available_collections():
    """Returns a list of available collection types."""
    return list(COLLECTION_REGISTRY.keys())
