"""Document loading and ingestion pipeline."""

__all__ = ["load_documents", "ingest_documents"]


def __getattr__(name: str):
    if name == "load_documents":
        from {{package_name}}.ingestion.loader import load_documents

        return load_documents
    if name == "ingest_documents":
        from {{package_name}}.ingestion.pipeline import ingest_documents

        return ingest_documents
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
