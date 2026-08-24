"""Ollama-backed embeddings.

Anthropic has no embeddings endpoint, so article text is vectorized with a
locally-run Ollama model (default ``qwen2.5``). Tune via settings / env:

    OLLAMA_BASE_URL    — e.g. http://localhost:11434
    OLLAMA_EMBED_MODEL — model tag that supports ``ollama embed``

Note: a dedicated embedding model (``nomic-embed-text``, ``mxbai-embed-large``,
``bge-m3``) is faster and cheaper than a chat model like ``qwen2.5``. If
``ollama embed`` rejects the model, switch ``OLLAMA_EMBED_MODEL`` to one of
those — the rest of this module needs no change.
"""
import logging

from django.conf import settings

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_EMBED_MODEL = getattr(settings, 'OLLAMA_EMBED_MODEL', 'nomic-embed-text')

_client = None


def get_client():
    global _client
    if _client is None:
        import ollama
        _client = ollama.Client(host=OLLAMA_BASE_URL)
    return _client


def embed_texts(texts):
    """Return a list of float vectors, one per input string.

    Returns an empty list on failure (e.g. Ollama not running) so that indexing
    and search degrade gracefully instead of raising.
    """
    texts = [t for t in texts if t and t.strip()]
    if not texts:
        return []
    try:
        resp = get_client().embed(model=OLLAMA_EMBED_MODEL, input=texts)
        return resp.get('embeddings', [])
    except Exception as exc:  # noqa: BLE001 — degrade, don't crash
        logger.warning('Ollama embed failed: %s', exc)
        return []


def embed_query(text):
    """Embed a single search query and return its vector (or [])."""
    embeds = embed_texts([text])
    return embeds[0] if embeds else []
