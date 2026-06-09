# MongoDB Vector Search Index (Manual Embeddings)

This scaffold uses **client-side** embeddings with `VoyageAIEmbeddings` (`voyage-4-lite`, 1024 dimensions by default). You must create a MongoDB Vector Search index that matches the embedding field LangChain writes.

## Index definition

```json
{
  "name": "vector_index",
  "type": "vectorSearch",
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "embedding",
        "numDimensions": 1024,
        "similarity": "cosine"
      },
      {
        "type": "filter",
        "path": "metadata.source"
      }
    ]
  }
}
```

If you change `VOYAGE_EMBEDDING_DIMENSIONS` or `VOYAGE_EMBEDDING_MODEL` in `.env`, update `numDimensions` to match.

## Create the index in Atlas

1. Open [MongoDB Atlas](https://cloud.mongodb.com) → your cluster → **Browse Collections**
2. Select database `rag_db` (or your `MONGODB_DATABASE`) and collection `documents`
3. Go to **Search Indexes** → **Create Search Index** → **JSON Editor**
4. Paste the definition above (or run `python scripts/create_vector_index.py` in your generated app)
5. Wait until index status is **Active** before running `ingest`

## Document shape after ingest

LangChain stores documents like:

```json
{
  "text": "chunk content...",
  "embedding": [0.012, -0.034, ...],
  "metadata": {
    "source": "data/sample/company-policy.txt"
  }
}
```

Field names `text` and `embedding` are the `MongoDBAtlasVectorSearch` defaults.

## References

- [MongoDB Vector Search overview](https://www.mongodb.com/docs/vector-search/)
- [LangChain MongoDB integration](https://www.mongodb.com/docs/atlas/ai-integrations/langchain/)
- [Voyage AI models](https://www.mongodb.com/docs/voyageai/)
