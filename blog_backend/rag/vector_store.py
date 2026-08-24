"""ChromaDB persistence layer.

Articles are stored as embedded chunks in a local Chroma collection. Chroma is
embedded (no separate server), so the vectors live in a folder on disk
(``CHROMA_PERSIST_DIR``) rather than in PostgreSQL. All chunks share a single
collection and are keyed by ``article_id`` + ``chunk_index``.
"""
import os
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

CHROMA_PERSIST_DIR = getattr(settings, 'CHROMA_PERSIST_DIR', None)
if CHROMA_PERSIST_DIR is None:
    CHROMA_PERSIST_DIR = os.path.join(settings.BASE_DIR, 'chroma_data')

COLLECTION_NAME = 'articles'

_client = None


def get_client():
    global _client
    if _client is None:
        import chromadb
        os.makedirs(CHROMA_PERSIST_DIR, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return _client


def get_collection():
    return get_client().get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={'hnsw:space': 'cosine'},
    )
