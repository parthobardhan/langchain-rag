"""Shared pytest fixtures."""

import pytest
from langchain_core.documents import Document
from langchain_core.runnables import RunnableLambda

from {{package_name}}.config import Settings


@pytest.fixture
def test_settings(monkeypatch) -> Settings:
    monkeypatch.setenv("MONGODB_URI", "mongodb://localhost:27017")
    monkeypatch.setenv("VOYAGE_API_KEY", "test-voyage-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    return Settings()


@pytest.fixture
def sample_documents() -> list[Document]:
    return [
        Document(
            page_content="Employees may work remotely up to three days per week.",
            metadata={"source": "policy.txt"},
        ),
        Document(
            page_content="Core collaboration hours are 10 AM to 3 PM local time.",
            metadata={"source": "policy.txt"},
        ),
    ]


@pytest.fixture
def mock_retriever(sample_documents):
    """LCEL-compatible retriever that returns fixed documents without calling MongoDB."""
    return RunnableLambda(lambda _query: sample_documents)
