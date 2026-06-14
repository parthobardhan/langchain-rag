# First contribution: add a PDF loader

Walk a new engineer through one concrete change using TDD.

**Run this inside a generated app** (e.g. `demo-docs-rag/`), not the `langchain-rag-scaffold` root. To change the template itself, edit files under `template/` and run `pytest -v` from the scaffold root.

## Prerequisites

```bash
pip install -e ".[dev]"
pytest tests/unit -v    # baseline should be green (generated app only)
```

## Step 1 — Write a failing test

Edit `tests/unit/test_ingestion.py`. Add a test that expects PDF loading:

```python
def test_load_documents_supports_pdf(tmp_path, mocker):
    pdf = tmp_path / "policy.pdf"
    pdf.write_bytes(b"%PDF-1.4 fake content for test")

    mocker.patch(
        "{{package_name}}.ingestion.loader._load_pdf",
        return_value=Document(page_content="policy text", metadata={"source": str(pdf)}),
    )

    docs = load_documents(pdf)
    assert len(docs) == 1
    assert docs[0].page_content == "policy text"
```

Run `pytest tests/unit/test_ingestion.py::test_load_documents_supports_pdf -v` — it should **fail** (function or PDF support missing).

## Step 2 — Implement the loader

If using an unfamiliar LangChain API, confirm its current signature via the `docs-langchain` MCP server before implementing.

Edit `src/<package>/ingestion/loader.py`:

1. Add `".pdf"` to `SUPPORTED_EXTENSIONS`
2. Add a `_load_pdf(path: Path) -> Document` helper (use a PDF library only if the team approves a new dependency; for the tutorial, a stub or minimal text extraction is fine)
3. Branch in `_load_file` or `load_documents` to call `_load_pdf` for `.pdf` files

Keep embedding and DB logic out of this module — loader returns `list[Document]` only.

## Step 3 — Green tests

```bash
pytest tests/unit -v
```

All unit tests should pass.

## Step 4 — Convention check

```bash
python scripts/check_conventions.py
```

Must exit 0. Do not use `langchain_classic`, `LLMChain`, `.run()`, `initialize_agent()`, or broken `langchain.*` imports.

## Step 5 — Optional integration check

If PDF ingestion hits Atlas:

```bash
pytest -m integration -v
```

## Checklist

- [ ] Failing unit test written first
- [ ] Implementation in `ingestion/loader.py` only
- [ ] `pytest tests/unit` passes
- [ ] `python scripts/check_conventions.py` passes
- [ ] No new dependencies unless added to allowlist test with team approval

## References

- `.cursor/skills/build-rag-app/SKILL.md` — extension workflows
- `.cursor/rules/langchain-conventions.mdc` — banned APIs
- `.cursor/rules/rag-project-structure.mdc` — module boundaries
