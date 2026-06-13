# New RAG App

Bootstrap a new LangChain RAG application from the langchain-rag-scaffold.

## Steps

1. Ask the engineer for an **app name** (directory) and optional **package name** (Python module, snake_case).
2. Run from the scaffold repo root:

```bash
python scripts/create_app.py <app-name> --package <package_name>
```

3. Tell the engineer to open the generated directory in Cursor (rules and skills are copied automatically).
4. Guide them through:
   - `pip install -e ".[dev]"`
   - `cp .env.example .env` and fill API keys
   - `pytest tests/unit`
   - `python scripts/create_vector_index.py`
   - `python -m <package>.cli ingest data/sample/`
   - `python -m <package>.cli query "..."`

## Defaults

- CLI only (ingest + query)
- Manual Voyage embeddings (`voyage-4-lite`, 1024 dims)
- MongoDB Atlas Vector Search
- OpenAI `ChatOpenAI` for generation

Do not add FastAPI or `langchain_classic` unless explicitly requested.
