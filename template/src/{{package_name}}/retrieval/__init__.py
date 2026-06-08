"""Vector store and retriever setup."""

__all__ = [
    "close_mongo_client",
    "delete_chunks_by_source",
    "get_embeddings",
    "get_mongo_client",
    "get_retriever",
    "get_vector_store",
]


def __getattr__(name: str):
    from {{package_name}}.retrieval import vector_store

    if name in __all__:
        return getattr(vector_store, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
