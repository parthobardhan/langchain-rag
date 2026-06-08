"""Split, embed, and store documents in MongoDB Vector Search."""

from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from {{package_name}}.config import Settings, get_settings
from {{package_name}}.ingestion.loader import load_documents
from {{package_name}}.retrieval.vector_store import (
    delete_chunks_by_source,
    get_embeddings,
    get_vector_store,
)


def split_documents(
    documents: list[Document],
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return splitter.split_documents(documents)


def ingest_documents(
    source_path: str | Path,
    *,
    settings: Settings | None = None,
    replace: bool = True,
) -> int:
    """Load, split, embed, and store documents. Returns number of chunks stored."""
    settings = settings or get_settings()
    documents = load_documents(source_path)
    chunks = split_documents(
        documents,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    if not chunks:
        raise ValueError(
            f"Loaded {len(documents)} document(s) from {source_path} but produced no chunks"
        )

    if replace:
        sources = list({doc.metadata["source"] for doc in documents})
        delete_chunks_by_source(sources, settings)

    embeddings = get_embeddings(settings)
    vector_store = get_vector_store(settings, embeddings)
    ids = vector_store.add_documents(chunks)
    return len(ids)
