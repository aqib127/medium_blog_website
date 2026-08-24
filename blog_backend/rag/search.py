"""Semantic search over the article vector store."""
import logging

from .embeddings import embed_query
from .vector_store import get_collection

logger = logging.getLogger(__name__)


def semantic_search(query, limit=5):
    """Return article summaries most semantically similar to `query`.

    Chunks are de-duplicated by ``article_id`` so a single long article isn't
    returned multiple times. Scores are cosine similarity (``1 - distance``).
    """
    if not query or not query.strip():
        return []

    vec = embed_query(query)
    if not vec:
        logger.warning('Semantic search unavailable: empty embedding for query.')
        return []

    try:
        results = get_collection().query(
            query_embeddings=[vec],
            n_results=min(limit * 3, 30),
            include=['documents', 'metadatas', 'distances'],
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning('Chroma query failed: %s', exc)
        return []

    docs = results.get('documents', [[]])[0]
    metas = results.get('metadatas', [[]])[0]
    dists = results.get('distances', [[]])[0]

    seen = {}
    for doc, meta, dist in zip(docs, metas, dists):
        article_id = meta.get('article_id')
        if article_id is None or article_id in seen:
            continue
        seen[article_id] = {
            'id': article_id,
            'title': meta.get('title', ''),
            'author': meta.get('author', ''),
            'tags': [t for t in (meta.get('tags') or '').split(', ') if t],
            'snippet': (doc or '')[:300],
            'score': round(1 - float(dist), 4) if dist is not None else None,
        }
        if len(seen) >= limit:
            break

    return list(seen.values())
