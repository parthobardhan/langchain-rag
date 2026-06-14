# First Contribution

Step-by-step TDD walkthrough: add PDF support to the document loader in **{{app_name}}**.

## Goal

Extend `src/{{package_name}}/ingestion/loader.py` so `ingest` can load `.pdf` files alongside `.txt` and `.md`.

## Steps

1. Read `AGENTS.md`, `.cursor/rules/rag-project-structure.mdc`, and `.cursor/rules/langchain-conventions.mdc`.

2. **Red** — Add a failing test in `tests/unit/test_ingestion.py`:
   - Create a minimal PDF in a temp directory (or use a small fixture file).
   - Call `load_documents` on the PDF path.
   - Assert one `Document` is returned with non-empty `page_content` and `metadata["source"]` set to the resolved path.

3. **Green** — Implement in `ingestion/loader.py`:
   - Add `.pdf` to `SUPPORTED_EXTENSIONS`.
   - Implement `{{package_name}}.ingestion.loader._load_pdf(path: Path) -> Document`.
   - Route PDF files through `_load_pdf` from `load_documents` (keep `_load_file` for text formats).
   - Query the `docs-langchain` MCP server (see `.cursor/mcp.json`) for the current recommended PDF parsing approach.
   - Use only approved dependencies from `pyproject.toml`; request approval before adding new ones.

4. **Refactor** — Keep loader helpers small; do not add ingestion logic to `cli.py`.

5. Verify:

```bash
pytest tests/unit/test_ingestion.py -v
python scripts/check_conventions.py
```

## Conventions

- Return `list[Document]` with `metadata["source"]` on every chunk.
- LCEL and `.invoke()` only — no `langchain_classic`, `LLMChain`, or `.run()`.
- LangChain API questions: use the `docs-langchain` MCP server, not web search.
