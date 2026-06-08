"""End-to-end integration tests against MongoDB Atlas and live APIs."""

import importlib
import os

import pytest

PACKAGE_NAME = "{{package_name}}"
rag = importlib.import_module(f"{PACKAGE_NAME}.chains.rag")
config = importlib.import_module(f"{PACKAGE_NAME}.config")
pipeline = importlib.import_module(f"{PACKAGE_NAME}.ingestion.pipeline")
vector_store = importlib.import_module(f"{PACKAGE_NAME}.retrieval.vector_store")

build_rag_chain = rag.build_rag_chain
Settings = config.Settings
ingest_documents = pipeline.ingest_documents
delete_chunks_by_source = vector_store.delete_chunks_by_source
get_retriever = vector_store.get_retriever

pytestmark = pytest.mark.integration

REQUIRED_ENV = ("MONGODB_URI", "VOYAGE_API_KEY", "OPENAI_API_KEY")


def _integration_enabled() -> bool:
    return all(os.getenv(key) for key in REQUIRED_ENV)


@pytest.fixture
def live_settings() -> Settings:
    if not _integration_enabled():
        pytest.skip("Set MONGODB_URI, VOYAGE_API_KEY, and OPENAI_API_KEY to run integration tests")
    return Settings()


def test_ingest_and_query_sample_docs(live_settings, tmp_path):
    sample = tmp_path / "integration.txt"
    sample.write_text(
        "The integration test document states that penguins cannot fly.",
        encoding="utf-8",
    )
    source = str(sample.resolve())

    try:
        count = ingest_documents(sample, settings=live_settings)
        assert count >= 1

        retriever = get_retriever(live_settings)
        chain = build_rag_chain(retriever, settings=live_settings)
        answer = chain.invoke("Can penguins fly according to the document?")

        assert isinstance(answer, str)
        assert answer.strip()
    finally:
        delete_chunks_by_source([source], live_settings)
