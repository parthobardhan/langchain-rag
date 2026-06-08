"""Unit tests for the RAG chain (no external API calls)."""

from unittest.mock import patch

from langchain_core.language_models.fake_chat_models import FakeListChatModel

from {{package_name}}.chains.rag import _format_docs, build_rag_chain


def test_format_docs_joins_page_content(sample_documents):
    result = _format_docs(sample_documents)
    assert "remote" in result
    assert "collaboration" in result


@patch("{{package_name}}.chains.rag.ChatOpenAI")
def test_build_rag_chain_invoke_returns_string(
    mock_chat_openai, mock_retriever, test_settings
):
    mock_chat_openai.return_value = FakeListChatModel(
        responses=["Remote work is allowed up to three days per week."]
    )

    chain = build_rag_chain(mock_retriever, settings=test_settings)
    answer = chain.invoke("What is the remote work policy?")

    mock_chat_openai.assert_called_once_with(
        model=test_settings.openai_model,
        temperature=0,
        api_key=test_settings.openai_api_key,
    )
    assert isinstance(answer, str)
    assert "three days" in answer.lower()
