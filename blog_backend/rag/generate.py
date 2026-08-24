"""RAG answer generation via a local Ollama chat model.

Retrieves the most relevant article chunks from the vector store and asks a
small local model (``OLLAMA_CHAT_MODEL``, default ``qwen2.5:1.5b``) to answer
grounded in that context. Off-topic questions are answered with a fixed error
string. If generation fails (model missing / Ollama down), it degrades to an
extractive answer listing the matched articles.

Note: the relevance gate works correctly only when the indexed articles contain
real content — against lorem-ipsum seed data every query is roughly equidistant,
so the model is the more reliable judge than a similarity threshold.
"""
import logging

from django.conf import settings

from .search import semantic_search

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_CHAT_MODEL = getattr(settings, 'OLLAMA_CHAT_MODEL', 'qwen2.5:1.5b')
MIN_SIMILARITY = getattr(settings, 'RAG_MIN_SIMILARITY', 0.45)

OFF_TOPIC_REPLY = "Sorry, I can only answer questions about this website."

_SYSTEM = (
    "You are a helpful assistant for a blog website. Answer the user's question "
    "Read the longest articles from this website if user asks "
    "using ONLY the article content provided below. Be concise and factual. "
    "If the question is not related to this website's articles or content, reply "
    "EXACTLY with: 'Sorry, I can only answer questions about this website.'"
)


def _chat(messages):
    import ollama
    client = ollama.Client(host=OLLAMA_BASE_URL)
    return client.chat(
        model=OLLAMA_CHAT_MODEL,
        messages=messages,
        options={'temperature': 0.3},
    )


def _extractive(results):
    lines = ["Here are the most relevant articles:"]
    for r in results:
        tags = ', '.join(r['tags']) or 'none'
        lines.append(f"- {r['title']} (by {r['author']}; tags: {tags})")
        lines.append(f"  {r['snippet']}")
    return "\n".join(lines)


def answer_with_rag(query, limit=5):
    """Return a grounded answer for `query`, or the off-topic error string."""
    results = semantic_search(query, limit=limit)
    if not results:
        return OFF_TOPIC_REPLY

    if (results[0].get('score') or 0) < MIN_SIMILARITY:
        return OFF_TOPIC_REPLY

    context = "\n\n".join(
        f"Title: {r['title']}\nTags: {', '.join(r['tags'])}\n{r['snippet']}"
        for r in results
    )

    try:
        resp = _chat([
            {'role': 'system', 'content': _SYSTEM},
            {'role': 'user', 'content': f"ARTICLES:\n{context}\n\nQUESTION: {query}"},
        ])
        answer = resp['message']['content'].strip()
        return answer or OFF_TOPIC_REPLY
    except Exception as exc:  # noqa: BLE001 — degrade gracefully
        logger.warning('Local generation failed: %s', exc)
        return _extractive(results)
