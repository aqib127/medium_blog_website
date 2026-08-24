"""Chunking + indexing of articles into the vector store."""
import re
import logging

from articles.models import Article

from .embeddings import embed_texts
from .vector_store import get_collection

logger = logging.getLogger(__name__)

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
_TAG_RE = re.compile(r'<[^>]+>')


def strip_html(text):
    """Strip HTML tags (Quill stores rich-text bodies) before embedding."""
    return _TAG_RE.sub(' ', text or '')


def _split_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into ~size-char windows with `overlap` chars of overlap."""
    text = re.sub(r'\s+', ' ', text).strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def build_chunks(article):
    """Return (texts, metadatas) pairs for a single article."""
    title = article.title or ''
    dek = strip_html(article.dek or '')
    body = strip_html(article.body or '')
    tags = [t.name for t in article.tags.all()]

    full = f'{title}. {dek} {body}'.strip()
    texts = _split_text(full)

    metadatas = []
    for i, text in enumerate(texts):
        metadatas.append({
            'article_id': article.id,
            'title': title,
            'chunk_index': i,
            'author': article.author.name if article.author_id else '',
            'tags': ', '.join(tags),
        })
    return texts, metadatas


def delete_article_chunks(article_id):
    """Remove all chunks for an article from the vector store."""
    try:
        collection = get_collection()
        existing = collection.get(
            where={'article_id': {'$eq': article_id}},
            include=['metadatas'],
        )
        ids = existing.get('ids', [])
        if ids:
            collection.delete(ids=ids)
    except Exception as exc:  # noqa: BLE001 — keep saves from breaking
        logger.warning('Could not delete chunks for article %s: %s', article_id, exc)


def index_article(article):
    """Re-embed and upsert a single article's chunks. Returns chunk count."""
    delete_article_chunks(article.id)

    texts, metadatas = build_chunks(article)
    if not texts:
        return 0

    embeddings = embed_texts(texts)
    if not embeddings or len(embeddings) != len(texts):
        logger.warning('Skipping article %s: no embeddings returned.', article.id)
        return 0

    ids = [f'article_{article.id}_chunk_{i}' for i in range(len(texts))]
    get_collection().upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    return len(ids)


def index_all_articles():
    """Re-index every published article. Returns the number of chunks."""
    articles = Article.objects.filter(status='published')
    total = 0
    count = articles.count()
    for article in articles.iterator():
        total += index_article(article)
    logger.info('Indexed %d chunks from %d published articles.', total, count)
    return total
