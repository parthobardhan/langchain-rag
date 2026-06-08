"""Load documents from local files."""

from pathlib import Path

from langchain_core.documents import Document

SUPPORTED_EXTENSIONS = {".txt", ".md"}


def _load_file(path: Path) -> Document:
    content = path.read_text(encoding="utf-8")
    return Document(
        page_content=content,
        metadata={"source": str(path.resolve())},
    )


def load_documents(source_path: str | Path) -> list[Document]:
    """Load text documents from a file or directory."""
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Source path does not exist: {path}")

    if path.is_file():
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported file type: {path.suffix}")
        return [_load_file(path)]

    documents: list[Document] = []
    for file_path in sorted(path.rglob("*")):
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            documents.append(_load_file(file_path))

    if not documents:
        extensions = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(
            f"No supported documents found in {path}. Supported extensions: {extensions}"
        )

    return documents
