# langchain-rag-scaffold

Scaffold for building **CLI-based RAG applications** with approved org technologies:

- **LangChain** (LCEL)
- **MongoDB Atlas Vector Search** (data + vector store)
- **Voyage AI** embeddings ([`voyage-4-lite`](https://docs.langchain.com/oss/python/integrations/embeddings/voyageai))
- **OpenAI** LLM (`ChatOpenAI`)

This repository is the **scaffold**, not a finished app. Engineers run the bootstrap script once to generate their own project.

## Create a new RAG app

```bash
python scripts/create_app.py acme-docs-rag --package acme_docs_rag
cd ../acme-docs-rag
```

The **directory name** can use hyphens (`acme-docs-rag`); the **Python package** and `pyproject.toml` project name use underscores (`acme_docs_rag`). If you omit `--package`, it is derived automatically from the app name.

In Cursor, use `/new-rag-app` to have the agent run this workflow.

The generated app includes:

- `ingest` and `query` CLI commands
- Unit tests (mocked, no live API keys — install deps with `pip install -e ".[dev]"`)
- Integration test stubs (Atlas + API keys)
- Cursor rules, skills, commands, hooks, MCP config, and Bugbot checklist copied from this repo

## Generated app setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env          # MONGODB_URI, VOYAGE_API_KEY, OPENAI_API_KEY
pytest tests/unit
python scripts/create_vector_index.py
python -m acme_docs_rag.cli ingest data/sample/
python -m acme_docs_rag.cli query "How many remote days are allowed?"
```

## Documentation

| Doc | Audience |
|-----|----------|
| [docs/engineer-guide.md](docs/engineer-guide.md) | Engineers building apps |
| [docs/mongodb-vector-index.md](docs/mongodb-vector-index.md) | Atlas index setup |

## Cursor features

| Feature | Location | Purpose |
|---------|----------|---------|
| Rules | `.cursor/rules/` | LangChain conventions + project layout |
| Skill | `.cursor/skills/build-rag-app/` | Agent workflow for extending apps |
| Commands | `.cursor/commands/` | `/new-rag-app` bootstrap; `first-contribution` for scaffold PRs |
| Hooks | `.cursor/hooks.json` | Auto-run conventions checker after agent edits |
| MCP | `.cursor/mcp.json` | Bundled LangChain docs server (`docs-langchain`) |
| Bugbot | `.cursor/BUGBOT.md` | PR review checklist for LangChain conventions |
| Plugin | `.cursor-plugin/plugin.json` | Optional org marketplace distribution |

The bundled `docs-langchain` MCP is enabled automatically in generated apps. Optionally install the **MongoDB Cursor plugin** from the marketplace to inspect Atlas indexes and collections via MCP.

## Developing the scaffold

This repo is not a generated app. Its tests live in `tests/` (bootstrap, hooks, smoke), not `tests/unit/`.

```bash
pip install -e ".[dev]"
pytest -v                              # scaffold tests (38)
SKIP_SMOKE_TESTS=1 pytest -v           # skip slow generated-app smoke test
```

`pytest tests/unit` is for **generated apps** only (copied from `template/tests/unit/`). Run that command inside your bootstrapped app directory (e.g. `demo-docs-rag/`), not here.

## Scaffold layout

```
langchain-rag-scaffold/
├── scripts/create_app.py    # bootstrap script
├── template/                # copied into new apps
├── docs/                    # scaffold-level docs
└── .cursor/                 # copied into new apps
```

## Conventions

- LCEL only: `prompt | llm | StrOutputParser()`
- No `langchain_classic`, `LLMChain`, `.run()`, or `initialize_agent()`
- Manual client-side embeddings with `voyage-4-lite` (1024 dimensions, works on standard Atlas clusters)

## Python version note

`langchain-voyageai>=0.2.0` (with `output_dimension` support) requires Python 3.11–3.12. On Python 3.13+, the template falls back to `langchain-voyageai>=0.1.3` — `voyage-4-lite` is still used; dimensions default to 1024 via the Voyage API.

## References

- [MongoDB Vector Search](https://www.mongodb.com/docs/vector-search/)
- [Voyage AI by MongoDB](https://www.mongodb.com/docs/voyageai/)
- [LangChain MongoDB integration](https://www.mongodb.com/docs/atlas/ai-integrations/langchain/)
- [Cursor Plugins](https://cursor.com/docs/plugins)
