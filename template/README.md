# {{app_name}}

LangChain RAG application generated from the [langchain-rag](https://github.com/your-org/langchain-rag) scaffold.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in API keys and MongoDB URI
pytest tests/unit
python scripts/create_vector_index.py
python -m {{package_name}}.cli ingest data/sample/
python -m {{package_name}}.cli query "How many remote days are allowed?"
```

See [docs/engineer-guide.md](docs/engineer-guide.md) for the full workflow.

## Project layout

| Path | Purpose |
|------|---------|
| `src/{{package_name}}/config.py` | Environment configuration |
| `src/{{package_name}}/ingestion/` | Load, split, and store documents |
| `src/{{package_name}}/retrieval/` | MongoDB Vector Search setup |
| `src/{{package_name}}/chains/` | LCEL RAG chain |
| `src/{{package_name}}/cli.py` | `ingest` and `query` commands |
| `tests/unit/` | Fast tests with mocks (no live API keys; deps required) |
| `tests/integration/` | Atlas + API tests (run when configured) |
