# Engineer Guide: Building a RAG App

This guide is for engineers using the **langchain-rag-scaffold**. You do not need to read the entire scaffold repository — follow the steps below.

## Prerequisites

- Python 3.11+
- MongoDB Atlas cluster with Vector Search enabled
- [Voyage AI API key](https://www.mongodb.com/docs/voyageai/) (embeddings)
- OpenAI API key (LLM)
- Optional: [MongoDB Cursor plugin](https://cursor.com/marketplace) for index inspection via MCP

## Step 1: Generate your app

```bash
git clone <org>/langchain-rag-scaffold
cd langchain-rag-scaffold
python scripts/create_app.py acme-docs-rag --package acme_docs_rag
cd ../acme-docs-rag
```

**Cursor tip:** Open the generated app directory as its own workspace root (File → Open Folder). This keeps agent context limited to this app and approved docs.

The directory name may use hyphens; the Python package and `pyproject.toml` project name use underscores. Omit `--package` to derive it from the app name.

In Cursor, you can also run the `/new-rag-app` command and ask the agent to run the bootstrap script.

## Step 2: Install and configure

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
```

Fill in `.env`:

| Variable | Description |
|----------|-------------|
| `MONGODB_URI` | Atlas connection string |
| `VOYAGE_API_KEY` | Voyage AI embeddings key |
| `OPENAI_API_KEY` | OpenAI key for `ChatOpenAI` |

## Step 3: Test-driven development loop

Start with unit tests — they run without Atlas or live API keys, but require project dependencies installed (`pip install -e ".[dev]"`):

```bash
pytest tests/unit -v
```

Unit tests use mocks for the retriever and LLM; they do not call Voyage, OpenAI, or MongoDB. Extend them as you add features:

1. Write a failing test in `tests/unit/`
2. Implement the feature in the matching `src/` module
3. Run `pytest tests/unit` until green

## Step 4: Create the vector search index

```bash
python scripts/create_vector_index.py
```

Follow the printed instructions or see [mongodb-vector-index.md](mongodb-vector-index.md).

## Step 5: Ingest and query

```bash
python -m acme_docs_rag.cli ingest data/sample/
python -m acme_docs_rag.cli query "How many remote days are allowed?"
```

Replace `acme_docs_rag` with your package name.

## Step 6: Integration tests (optional)

After Atlas and API keys are configured:

```bash
pytest -m integration -v
```

## Where to make changes

| Task | Edit this file |
|------|----------------|
| Change chunk size | `src/<package>/config.py` |
| Support new file types | `src/<package>/ingestion/loader.py` |
| Change RAG prompt | `src/<package>/chains/rag.py` |
| Add metadata filters | `src/<package>/retrieval/vector_store.py` + index definition |
| Add CLI commands | `src/<package>/cli.py` |

## LangChain conventions

Cursor rules in `.cursor/rules/` enforce:

- LCEL chains: `prompt | llm | StrOutputParser()`
- `RunnableWithMessageHistory` for chat memory (if you add it later)
- No `langchain_classic`, `LLMChain`, `.run()`, or `initialize_agent()`

Use `/build-rag-app` in Cursor when you need agent help extending the app.
