# RAG — Retrieval-Augmented Generation for the blog

Adds semantic (vector) search over articles so the chatbot can answer by
*meaning*, not just keyword matching.

## How it works

1. **Embeddings** — article text is turned into vectors with a local
   [Ollama](https://ollama.com) model (`nomic-embed-text`). Anthropic has no
   embeddings endpoint, so this is a separate, locally-hosted model.
2. **Vector store** — vectors + text chunks are stored in an embedded
   [ChromaDB](https://docs.trychroma.com) collection on disk (default
   `blog_backend/chroma_data/`), keyed by `article_id`.
3. **Retrieval** — the chatbot's `search_articles_semantic` tool embeds the
   query and returns the most similar article chunks.
4. **Generation** — a local Ollama chat model (`qwen2.5:1.5b`) answers grounded
   in the retrieved chunks. Off-topic questions get a fixed error reply.

## Setup

```bash
# 1. Install the Python deps
pip install chromadb ollama

# 2. Run Ollama locally and pull the models
ollama pull nomic-embed-text      # embeddings (274 MB)
ollama pull qwen2.5:1.5b          # answer generation (986 MB)

# 3. Index all published articles into ChromaDB
python manage.py index_articles
```

## Configuration (env, in `.env`)

| Variable | Default | Meaning |
| --- | --- | --- |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server address |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model used for embeddings |
| `OLLAMA_CHAT_MODEL` | `qwen2.5:1.5b` | Model used to generate answers |
| `RAG_MIN_SIMILARITY` | `0.45` | Cosine threshold below which a query is treated as off-topic |
| `CHROMA_PERSIST_DIR` | `blog_backend/chroma_data/` | Where vectors are stored on disk |

## Keeping the index in sync

`rag/signals.py` re-embeds an article whenever it is published/edited and
removes it on unpublish/delete. If the index ever gets out of sync (or Ollama
was down during a save), rebuild it manually:

```bash
python manage.py index_articles
```

## API endpoints

- `POST /api/v1/rag/search/` — semantic search. Body `{"query": "...", "limit": 5}`
- `POST /api/v1/rag/reindex/` — admin-only full reindex.

## Notes

- **Embeddings happen synchronously on save.** For a small site this is fine;
  for heavy write traffic, defer indexing to a background task (Celery/Django Q).
- **Relevance gate needs real content.** The similarity threshold (and the
  off-topic error) only cleanly separates relevant from irrelevant queries once
  the indexed articles contain real text — against lorem-ipsum seed data every
  query is roughly equidistant. Tune `RAG_MIN_SIMILARITY` to taste.
- **Keep the chat model small.** `qwen2.5:1.5b` (~1 GB) fits in low-RAM hosts;
  the full `qwen2.5` (4.7 GB) OOMs on a 7 GB machine.
- Failures are non-fatal: if Ollama or Chroma is unavailable, indexing/search
  degrade gracefully (logged warnings) and article saves still succeed.
