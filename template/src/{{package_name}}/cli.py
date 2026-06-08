"""CLI for ingesting documents and querying the RAG chain."""

from pathlib import Path

import typer
from dotenv import load_dotenv

from {{package_name}}.chains.rag import build_rag_chain
from {{package_name}}.config import get_settings
from {{package_name}}.ingestion.pipeline import ingest_documents
from {{package_name}}.retrieval.vector_store import get_retriever

load_dotenv()

app = typer.Typer(help="{{app_name}} — LangChain RAG CLI")


@app.command()
def ingest(
    source: Path = typer.Argument(..., help="File or directory of documents to ingest"),
    replace: bool = typer.Option(
        True,
        "--replace/--append",
        help="Replace existing chunks for the same source files (default: replace)",
    ),
) -> None:
    """Load, split, embed, and store documents in MongoDB."""
    try:
        count = ingest_documents(source, replace=replace)
    except (FileNotFoundError, ValueError) as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"Ingested {count} chunks from {source}")


@app.command()
def query(
    question: str = typer.Argument(..., help="Question to ask the RAG chain"),
) -> None:
    """Query the RAG chain with a natural-language question."""
    settings = get_settings()
    retriever = get_retriever(settings)
    chain = build_rag_chain(retriever, settings=settings)
    answer = chain.invoke(question)
    typer.echo(answer)


if __name__ == "__main__":
    app()
