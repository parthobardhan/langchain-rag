# MongoDB Vector Search Index

Manual embeddings with `voyage-4-lite` (default 1024 dimensions).

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

Run `python scripts/create_vector_index.py` to print a customized definition from your `.env`.

## Atlas steps

1. Browse Collections → select your database and collection
2. Search Indexes → Create Search Index → JSON Editor
3. Paste the definition and wait for **Active** status

References: [Vector Search](https://www.mongodb.com/docs/vector-search/) · [LangChain integration](https://www.mongodb.com/docs/atlas/ai-integrations/langchain/)
