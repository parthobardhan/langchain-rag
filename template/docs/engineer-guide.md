# Engineer Guide: {{app_name}}

**Cursor tip:** Open this app directory as its own workspace root (File → Open Folder). This keeps agent context limited to this app and approved docs.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
pytest tests/unit -v
python scripts/create_vector_index.py
python -m {{package_name}}.cli ingest data/sample/
python -m {{package_name}}.cli query "How many remote days are allowed?"
```

## TDD workflow

Unit tests use mocks and do not call Voyage, OpenAI, or MongoDB, but require `pip install -e ".[dev]"` first.

1. Write failing tests in `tests/unit/`
2. Implement in the matching `src/{{package_name}}/` module
3. Run `pytest tests/unit` until green
4. Run `pytest -m integration` after Atlas is configured

## Where to make changes

| Task | File |
|------|------|
| Config / env vars | `src/{{package_name}}/config.py` |
| Load new file types | `src/{{package_name}}/ingestion/loader.py` |
| Chunking / ingest | `src/{{package_name}}/ingestion/pipeline.py` |
| Vector store | `src/{{package_name}}/retrieval/vector_store.py` |
| RAG prompt | `src/{{package_name}}/chains/rag.py` |
| CLI commands | `src/{{package_name}}/cli.py` |

## Integration tests

Set `MONGODB_URI`, `VOYAGE_API_KEY`, and `OPENAI_API_KEY` in `.env`, then:

```bash
pytest -m integration -v
```

See [mongodb-vector-index.md](mongodb-vector-index.md) for index setup.
