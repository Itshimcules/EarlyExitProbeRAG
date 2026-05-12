# Vector Database Adapter

`ChromaWikiSearch` is the first real vector database adapter behind the same retrieval surface as keyword search and the dependency-free JSON vector index.

## Install

```bash
pip install '.[vector-db]'
```

## Run

```bash
RETRIEVAL_MODE=chroma \
CHROMA_PERSIST_PATH=.cache/chroma \
CHROMA_COLLECTION=synthetic_technician_wiki \
uvicorn app.main:app --reload
```

## Interface

The harness expects retrieval adapters to provide:

- `search(query: str, top_k: int)`
- `get_page(page_id: str)`
- `page_ids()`
- `related_page_ids(page)`

That lets the app switch between:

- `KeywordWikiSearch`
- `PersistentVectorWikiSearch`
- `ChromaWikiSearch`

without changing FastAPI routes or prompt logic.

## Embeddings

The default Chroma adapter uses `HashingEmbeddingFunction`, a deterministic local embedding function. It is intentionally lightweight so the demo does not download embedding models or call external services.

For production-like experiments, replace the embedding function with a model-backed embedding function while preserving the `ChromaWikiSearch` interface.

