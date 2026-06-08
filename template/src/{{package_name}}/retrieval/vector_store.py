"""MongoDB Atlas Vector Search factory functions."""

import inspect
import warnings
from functools import lru_cache

from langchain_core.vectorstores import VectorStoreRetriever
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_voyageai import VoyageAIEmbeddings
from pymongo import MongoClient

from {{package_name}}.config import Settings, get_settings


@lru_cache(maxsize=4)
def get_mongo_client(uri: str) -> MongoClient:
    """Return a cached MongoClient for the given URI."""
    return MongoClient(uri)


def close_mongo_client() -> None:
    """Clear the cached MongoClient (useful in tests)."""
    get_mongo_client.cache_clear()


def get_mongo_collection(settings: Settings):
    client = get_mongo_client(settings.mongodb_uri)
    return client[settings.mongodb_database][settings.mongodb_collection]


def delete_chunks_by_source(sources: list[str], settings: Settings) -> int:
    """Remove stored chunks whose source is in sources. Returns delete count."""
    if not sources:
        return 0
    collection = get_mongo_collection(settings)
    result = collection.delete_many({"source": {"$in": sources}})
    return result.deleted_count


def _embedding_kwargs(settings: Settings) -> dict:
    """Build VoyageAIEmbeddings kwargs, handling output_dimension across package versions."""
    kwargs: dict = {
        "model": settings.voyage_embedding_model,
        "voyage_api_key": settings.voyage_api_key,
    }
    params = inspect.signature(VoyageAIEmbeddings).parameters
    if "output_dimension" in params:
        kwargs["output_dimension"] = settings.voyage_embedding_dimensions
    elif settings.voyage_embedding_dimensions != 1024:
        warnings.warn(
            "VOYAGE_EMBEDDING_DIMENSIONS is set but this langchain-voyageai version "
            "does not support output_dimension; ensure your Atlas index numDimensions "
            "matches the model default (1024 for voyage-4-lite).",
            stacklevel=3,
        )
    return kwargs


def get_embeddings(settings: Settings) -> VoyageAIEmbeddings:
    """Create VoyageAIEmbeddings using voyage-4-lite (default 1024 dimensions)."""
    return VoyageAIEmbeddings(**_embedding_kwargs(settings))


def get_vector_store(
    settings: Settings,
    embeddings: VoyageAIEmbeddings,
) -> MongoDBAtlasVectorSearch:
    collection = get_mongo_collection(settings)
    return MongoDBAtlasVectorSearch(
        collection=collection,
        embedding=embeddings,
        index_name=settings.vector_index_name,
    )


def get_retriever(settings: Settings | None = None) -> VectorStoreRetriever:
    settings = settings or get_settings()
    embeddings = get_embeddings(settings)
    vector_store = get_vector_store(settings, embeddings)
    return vector_store.as_retriever(search_kwargs={"k": settings.retrieval_k})
