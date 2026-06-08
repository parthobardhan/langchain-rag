---
name: build-rag-app
description: Guide engineers through extending a LangChain RAG app generated from the langchain-rag scaffold. Use when adding loaders, changing prompts, configuring MongoDB Vector Search, writing tests, or implementing ingestion/retrieval features.
---

# Build RAG App

## Before coding

1. Read `README.md` and `.env.example` in the generated app
2. Identify which module owns the change (see `.cursor/rules/rag-project-structure.mdc`)
3. Write or update a unit test in `tests/unit/` first

## Common tasks

### Add a new document source

1. Extend `ingestion/loader.py` — return `list[Document]` with `metadata["source"]`
2. Add unit test in `tests/unit/test_ingestion.py`
3. Run `pytest tests/unit`

### Change the RAG prompt

1. Edit `chains/rag.py` — only the `ChatPromptTemplate`
2. Update `tests/unit/test_rag_chain.py` if behavior changes
3. Never move prompt logic into `cli.py`

### Add metadata pre-filters

1. Add filter field to vector index (see `docs/mongodb-vector-index.md`)
2. Pass `search_kwargs` with MQL filter in `retrieval/vector_store.py`
3. Add integration test if filter behavior is critical

### Ingest new data

```bash
python -m <package>.cli ingest path/to/docs/
```

### Debug retrieval

1. Verify vector index is **Active** in Atlas
2. Confirm `VOYAGE_EMBEDDING_DIMENSIONS` matches index `numDimensions`
3. Use MongoDB MCP to inspect collection documents and indexes

## TDD checklist

```
- [ ] Failing unit test written
- [ ] Implementation in correct module
- [ ] pytest tests/unit passes
- [ ] Integration test added if Atlas-dependent
```

## References

- [MongoDB Vector Search](https://www.mongodb.com/docs/vector-search/)
- [LangChain MongoDB integration](https://www.mongodb.com/docs/atlas/ai-integrations/langchain/)
- [Voyage AI models](https://www.mongodb.com/docs/voyageai/)
