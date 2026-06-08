#!/usr/bin/env python3
"""Print MongoDB Vector Search index definition for manual Voyage embeddings."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

VECTOR_INDEX_NAME = os.getenv("VECTOR_INDEX_NAME", "vector_index")
EMBEDDING_DIMENSIONS = int(os.getenv("VOYAGE_EMBEDDING_DIMENSIONS", "1024"))


def build_index_definition() -> dict:
    return {
        "name": VECTOR_INDEX_NAME,
        "type": "vectorSearch",
        "definition": {
            "fields": [
                {
                    "type": "vector",
                    "path": "embedding",
                    "numDimensions": EMBEDDING_DIMENSIONS,
                    "similarity": "cosine",
                },
                {
                    "type": "filter",
                    "path": "metadata.source",
                },
            ]
        },
    }


def main() -> int:
    index_def = build_index_definition()
    print("MongoDB Vector Search index definition:\n")
    print(json.dumps(index_def, indent=2))
    print(
        """

Create this index in MongoDB Atlas:
  1. Open your cluster in Atlas → Browse Collections → your collection
  2. Go to Search Indexes → Create Search Index → JSON Editor
  3. Paste the definition above and create the index
  4. Wait until the index status is Active before running ingest

See docs/mongodb-vector-index.md for details.
"""
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
