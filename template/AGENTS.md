# {{app_name}} — agent guide

This is a **generated LangChain RAG application** bootstrapped from the langchain-rag-scaffold.

## Module layout

| Module | Responsibility |
|--------|----------------|
| `src/{{package_name}}/ingestion/loader.py` | Load files → `Document` list |
| `src/{{package_name}}/ingestion/pipeline.py` | Split, embed, store |
| `src/{{package_name}}/retrieval/vector_store.py` | MongoDB + Voyage setup |
| `src/{{package_name}}/chains/rag.py` | LCEL RAG chain |
| `src/{{package_name}}/cli.py` | Typer CLI commands |

See `.cursor/rules/rag-project-structure.mdc` before adding features.

## Conventions

Follow `.cursor/rules/langchain-conventions.mdc`:

- LCEL only: `prompt | llm | StrOutputParser()`
- No `langchain_classic`, `LLMChain`, `.run()`, or `initialize_agent()`
- Use `.invoke()`, not `.run()`

After editing Python under `src/` or `tests/`:

```bash
python scripts/check_conventions.py
pytest tests/unit
```

## Approved context boundaries

Use **only**:

- This repository
- Official LangChain, MongoDB Atlas, and Voyage AI documentation

Do **not** import code or copy patterns from sibling projects. Keep changes within this app's modules and approved dependencies.

## First contribution

In Cursor, run `/first-contribution` for a step-by-step TDD walkthrough (add a PDF loader).
