"""Tests for template ingestion pipeline via a bootstrapped app."""

from __future__ import annotations

import importlib.util
import inspect
import sys
import warnings
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

SCAFFOLD_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SCAFFOLD_ROOT / "scripts"))

from create_app import create_app  # noqa: E402


def _load_module(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _install_langchain_mocks() -> None:
    if "langchain_mongodb" not in sys.modules:
        mock_mongodb = ModuleType("langchain_mongodb")
        mock_mongodb.MongoDBAtlasVectorSearch = MagicMock()
        sys.modules["langchain_mongodb"] = mock_mongodb
    if "langchain_voyageai" not in sys.modules:
        mock_voyage = ModuleType("langchain_voyageai")
        mock_voyage.VoyageAIEmbeddings = MagicMock()
        sys.modules["langchain_voyageai"] = mock_voyage


def _cleanup_test_rag_modules() -> None:
    for name in list(sys.modules):
        if name == "test_rag" or name.startswith("test_rag."):
            del sys.modules[name]


@pytest.fixture
def rag_app(tmp_path: Path):
    """Bootstrap a minimal RAG app and load pipeline modules without package __init__."""
    dest = create_app("test-rag", "test_rag", tmp_path, copy_cursor=False)
    pkg = dest / "src" / "test_rag"
    sys.path.insert(0, str(dest / "src"))
    _install_langchain_mocks()

    config = _load_module("test_rag.config", pkg / "config.py")
    _load_module("test_rag.ingestion.loader", pkg / "ingestion" / "loader.py")
    vector_store = _load_module(
        "test_rag.retrieval.vector_store", pkg / "retrieval" / "vector_store.py"
    )
    pipeline = _load_module("test_rag.ingestion.pipeline", pkg / "ingestion" / "pipeline.py")

    yield {
        "dest": dest,
        "pkg": pkg,
        "pipeline": pipeline,
        "vector_store": vector_store,
        "Settings": config.Settings,
    }

    sys.path.remove(str(dest / "src"))
    _cleanup_test_rag_modules()


def test_get_mongo_client_returns_cached_instance(rag_app):
    vs = rag_app["vector_store"]
    vs.close_mongo_client()
    uri = "mongodb://localhost:27017"

    client_a = vs.get_mongo_client(uri)
    client_b = vs.get_mongo_client(uri)

    assert client_a is client_b
    vs.close_mongo_client()


def test_delete_chunks_by_source_calls_delete_many(rag_app, monkeypatch):
    mock_collection = MagicMock()
    mock_collection.delete_many.return_value = MagicMock(deleted_count=3)
    monkeypatch.setattr(
        rag_app["vector_store"],
        "get_mongo_collection",
        lambda _settings: mock_collection,
    )

    settings = rag_app["Settings"](
        mongodb_uri="mongodb://localhost:27017",
        voyage_api_key="test-voyage-key",
        openai_api_key="test-openai-key",
    )
    deleted = rag_app["vector_store"].delete_chunks_by_source(
        ["/docs/policy.txt"], settings
    )

    mock_collection.delete_many.assert_called_once_with(
        {"metadata.source": {"$in": ["/docs/policy.txt"]}}
    )
    assert deleted == 3


def test_delete_chunks_by_source_noop_for_empty_list(rag_app, monkeypatch):
    mock_get_collection = MagicMock()
    monkeypatch.setattr(rag_app["vector_store"], "get_mongo_collection", mock_get_collection)

    settings = rag_app["Settings"](
        mongodb_uri="mongodb://localhost:27017",
        voyage_api_key="test-voyage-key",
        openai_api_key="test-openai-key",
    )
    deleted = rag_app["vector_store"].delete_chunks_by_source([], settings)

    mock_get_collection.assert_not_called()
    assert deleted == 0


@patch("test_rag.ingestion.pipeline.get_vector_store")
@patch("test_rag.ingestion.pipeline.get_embeddings")
@patch("test_rag.ingestion.pipeline.delete_chunks_by_source")
def test_ingest_documents_replace_deletes_by_source(
    mock_delete, mock_embeddings, mock_vector_store, rag_app, tmp_path
):
    sample = tmp_path / "note.txt"
    sample.write_text("Hello world.", encoding="utf-8")
    mock_vector_store.return_value.add_documents.return_value = ["id1"]

    settings = rag_app["Settings"](
        mongodb_uri="mongodb://localhost:27017",
        voyage_api_key="test-voyage-key",
        openai_api_key="test-openai-key",
    )
    count = rag_app["pipeline"].ingest_documents(
        sample, settings=settings, replace=True
    )

    mock_delete.assert_called_once()
    sources = mock_delete.call_args[0][0]
    assert str(sample.resolve()) in sources
    assert count == 1


@patch("test_rag.ingestion.pipeline.get_vector_store")
@patch("test_rag.ingestion.pipeline.get_embeddings")
@patch("test_rag.ingestion.pipeline.delete_chunks_by_source")
def test_ingest_documents_append_skips_delete(
    mock_delete, mock_embeddings, mock_vector_store, rag_app, tmp_path
):
    sample = tmp_path / "note.txt"
    sample.write_text("Hello world.", encoding="utf-8")
    mock_vector_store.return_value.add_documents.return_value = ["id1"]

    settings = rag_app["Settings"](
        mongodb_uri="mongodb://localhost:27017",
        voyage_api_key="test-voyage-key",
        openai_api_key="test-openai-key",
    )
    count = rag_app["pipeline"].ingest_documents(
        sample, settings=settings, replace=False
    )

    mock_delete.assert_not_called()
    assert count == 1


def test_load_documents_empty_directory_raises(rag_app, tmp_path):
    loader = sys.modules["test_rag.ingestion.loader"]
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()

    with pytest.raises(ValueError, match="No supported documents found"):
        loader.load_documents(empty_dir)


def test_ingest_documents_empty_directory_raises(rag_app, tmp_path):
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    settings = rag_app["Settings"](
        mongodb_uri="mongodb://localhost:27017",
        voyage_api_key="test-voyage-key",
        openai_api_key="test-openai-key",
    )

    with pytest.raises(ValueError, match="No supported documents found"):
        rag_app["pipeline"].ingest_documents(empty_dir, settings=settings)


def test_loader_import_does_not_load_langchain_mongodb(tmp_path):
    """Importing loader alone should not eagerly import langchain_mongodb."""
    dest = create_app("import-test", "import_test", tmp_path, copy_cursor=False)
    src = str(dest / "src")
    sys.path.insert(0, src)
    _cleanup_test_rag_modules()
    sys.modules.pop("langchain_mongodb", None)

    try:
        import import_test.ingestion.loader  # noqa: F401
    finally:
        sys.path.remove(src)
        _cleanup_test_rag_modules()
        for name in list(sys.modules):
            if name == "import_test" or name.startswith("import_test."):
                del sys.modules[name]

    assert "langchain_mongodb" not in sys.modules


def test_embedding_kwargs_includes_output_dimension_when_supported(rag_app):
    vs = rag_app["vector_store"]
    settings = rag_app["Settings"](
        mongodb_uri="mongodb://localhost:27017",
        voyage_api_key="test-voyage-key",
        openai_api_key="test-openai-key",
        voyage_embedding_dimensions=512,
    )

    def fake_signature(_cls):
        return inspect.Signature(
            parameters=[
                inspect.Parameter("model", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                inspect.Parameter(
                    "output_dimension", inspect.Parameter.POSITIONAL_OR_KEYWORD
                ),
                inspect.Parameter(
                    "voyage_api_key", inspect.Parameter.POSITIONAL_OR_KEYWORD
                ),
            ]
        )

    with patch.object(vs.inspect, "signature", fake_signature):
        kwargs = vs._embedding_kwargs(settings)

    assert kwargs["output_dimension"] == 512
    assert kwargs["voyage_api_key"] == "test-voyage-key"


def test_embedding_kwargs_warns_when_output_dimension_unsupported(rag_app):
    vs = rag_app["vector_store"]
    settings = rag_app["Settings"](
        mongodb_uri="mongodb://localhost:27017",
        voyage_api_key="test-voyage-key",
        openai_api_key="test-openai-key",
        voyage_embedding_dimensions=512,
    )

    def fake_signature(_cls):
        return inspect.Signature(
            parameters=[
                inspect.Parameter("model", inspect.Parameter.POSITIONAL_OR_KEYWORD),
                inspect.Parameter(
                    "voyage_api_key", inspect.Parameter.POSITIONAL_OR_KEYWORD
                ),
            ]
        )

    with patch.object(vs.inspect, "signature", fake_signature):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            kwargs = vs._embedding_kwargs(settings)

    assert "output_dimension" not in kwargs
    assert any("VOYAGE_EMBEDDING_DIMENSIONS" in str(w.message) for w in caught)
