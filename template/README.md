# {{app_name}}

LangChain RAG application generated from the [langchain-rag-scaffold](https://github.com/your-org/langchain-rag-scaffold).

Open this directory as its own Cursor workspace root to keep agent context within this app.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # fill in API keys and MongoDB URI
python -m {{package_name}}.cli ingest data/sample/
python -m {{package_name}}.cli query "How many remote days are allowed?"
```

## Project layout

| Path | Purpose |
|------|---------|
| `src/{{package_name}}/config.py` | Environment configuration |
| `src/{{package_name}}/ingestion/` | Load, split, and store documents |
| `src/{{package_name}}/retrieval/` | MongoDB Vector Search setup |
| `src/{{package_name}}/chains/` | LCEL RAG chain |
| `src/{{package_name}}/cli.py` | `ingest` and `query` commands |
| `data/sample/` | Sample documents for local testing |
