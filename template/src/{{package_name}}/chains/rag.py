"""RAG chain built with LangChain LCEL."""

from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_openai import ChatOpenAI

from {{package_name}}.config import Settings, get_settings


def _format_docs(docs: list[Any]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def build_rag_chain(
    retriever: Runnable,
    *,
    settings: Settings | None = None,
) -> Runnable:
    """Build an LCEL RAG chain from a retriever."""
    settings = settings or get_settings()

    llm = ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        api_key=settings.openai_api_key,
    )
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "Answer using only this context:\n{context}"),
            ("human", "{question}"),
        ]
    )

    return (
        {
            "context": retriever | _format_docs,
            "question": RunnablePassthrough(),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
