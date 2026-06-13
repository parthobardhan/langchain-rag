# langchain-rag-scaffold — agent guide

This repository is a **scaffold** for generating LangChain RAG CLI applications. It is not a runnable RAG app itself.

## What to do here

- Change the **template** (`template/`) that gets copied into new apps
- Change **bootstrap** logic (`scripts/create_app.py`)
- Change **Cursor guidance** (`.cursor/rules/`, `.cursor/skills/`, `.cursor/commands/`, hooks)
- Add or update **scaffold tests** (`tests/`)

## Conventions

Follow [.cursor/rules/langchain-conventions.mdc](.cursor/rules/langchain-conventions.mdc):

- LCEL only — no `langchain_classic`, `LLMChain`, `.run()`, or `initialize_agent()`
- Approved stack: `langchain_openai`, `langchain_core`, `langchain_mongodb`, `langchain_voyageai`

Run `python template/scripts/check_conventions.py --root template` when editing template `src/` or `tests/`.

## Approved context boundaries

Use **only**:

- This repository
- Official LangChain, MongoDB Atlas, and Voyage AI documentation (LangChain via the `docs-langchain` MCP server in `.cursor/mcp.json`)

Do **not** pull code, patterns, or dependencies from sibling projects or other internal repos unless explicitly requested. Generated apps must remain self-contained after bootstrap.

## Key files

| Path | Purpose |
|------|---------|
| `template/` | Generated app source |
| `scripts/create_app.py` | Bootstrap script |
| `template/scripts/check_conventions.py` | Banned API checker (canonical; run `scripts/sync_conventions.py` after edits) |
| `docs/maintainers.md` | Maintainer invariants |
| `docs/engineer-guide.md` | Engineer onboarding |

## Testing

```bash
pip install -e ".[dev]"
pytest -v
```

The smoke test bootstraps a full app and runs its unit tests — skip locally with `SKIP_SMOKE_TESTS=1` if needed.
