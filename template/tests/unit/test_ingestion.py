"""Unit tests for document loading and splitting."""

from pathlib import Path
from unittest.mock import patch

import pytest
from langchain_core.documents import Document

from {{package_name}}.ingestion.loader import load_documents
from {{package_name}}.ingestion.pipeline import ingest_documents, split_documents


def test_load_documents_from_file(tmp_path: Path):
    sample = tmp_path / "note.txt"
    sample.write_text("Hello from the sample file.", encoding="utf-8")

    docs = load_documents(sample)

    assert len(docs) == 1
    assert "Hello" in docs[0].page_content
    assert docs[0].metadata["source"] == str(sample.resolve())


def test_load_documents_from_directory(tmp_path: Path):
    (tmp_path / "a.txt").write_text("Document A", encoding="utf-8")
    (tmp_path / "b.md").write_text("Document B", encoding="utf-8")

    docs = load_documents(tmp_path)

    assert len(docs) == 2
    contents = {doc.page_content for doc in docs}
    assert "Document A" in contents
    assert "Document B" in contents


def test_split_documents_creates_chunks():
    documents = [
        Document(page_content="word " * 500, metadata={"source": "big.txt"}),
    ]

    chunks = split_documents(documents, chunk_size=200, chunk_overlap=20)

    assert len(chunks) > 1
    assert all(chunk.metadata["source"] == "big.txt" for chunk in chunks)


@patch("{{package_name}}.ingestion.pipeline.get_vector_store")
@patch("{{package_name}}.ingestion.pipeline.get_embeddings")
@patch("{{package_name}}.ingestion.pipeline.delete_chunks_by_source")
def test_ingest_documents_replace_deletes_by_source(
    mock_delete, mock_embeddings, mock_vector_store, tmp_path, test_settings
):
    sample = tmp_path / "note.txt"
    sample.write_text("Hello world.", encoding="utf-8")

    mock_vector_store.return_value.add_documents.return_value = ["id1"]

    count = ingest_documents(sample, settings=test_settings, replace=True)

    mock_delete.assert_called_once()
    sources = mock_delete.call_args[0][0]
    assert str(sample.resolve()) in sources
    assert count == 1


@patch("{{package_name}}.ingestion.pipeline.get_vector_store")
@patch("{{package_name}}.ingestion.pipeline.get_embeddings")
@patch("{{package_name}}.ingestion.pipeline.delete_chunks_by_source")
def test_ingest_documents_append_skips_delete(
    mock_delete, mock_embeddings, mock_vector_store, tmp_path, test_settings
):
    sample = tmp_path / "note.txt"
    sample.write_text("Hello world.", encoding="utf-8")

    mock_vector_store.return_value.add_documents.return_value = ["id1"]

    count = ingest_documents(sample, settings=test_settings, replace=False)

    mock_delete.assert_not_called()
    assert count == 1


def test_load_documents_empty_directory_raises(tmp_path: Path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(ValueError, match="No supported documents found"):
        load_documents(empty_dir)


def test_ingest_documents_empty_directory_raises(tmp_path: Path, test_settings):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(ValueError, match="No supported documents found"):
        ingest_documents(empty_dir, settings=test_settings)
