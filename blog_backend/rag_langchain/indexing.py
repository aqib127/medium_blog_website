import re
import logging
from django.conf import settings
from articles.models import Article
from .vectorstore import get_vectorstore

logger = logging.getLogger(__name__)

CHUNK_SIZE = settings.CHUNK_SIZE
CHUNK_OVERLAP = settings.CHUNK_OVERLAP
_TAG_RE = re.compile(r'<[^>]+>')

def strip_html(text):
    return _TAG_RE.sub(' ', text or '')

def split_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
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
    title = article.title or ''
    dek = strip_html(article.dek or '')
    body = strip_html(article.body or '')
    tags = [t.name for t in article.tags.all()]
    full = f"{title}. {dek} {body}".strip()
    texts = split_text(full)

    metadatas = []
    for i, text in enumerate(texts):
        metadatas.append({
            'article_id': str(article.id),
            'title': title,
            'chunk_index': i,
            'author': article.author.name if article.author_id else '',
            'tags': ', '.join(tags),
            # NEW: include popularity metrics so the model can answer "most liked/commented"
            'claps_count': article.claps_count,
            'comments_count': article.comments_count,
            # If you have a 'views' field, add it here
        })
    return texts, metadatas

def delete_article_chunks(article_id):
    """Remove all chunks for an article from the vector store."""
    vectorstore = get_vectorstore()
    try:
        vectorstore.delete(filter={"article_id": str(article_id)})
    except Exception as e:
        logger.warning(f"Delete chunks failed for article {article_id}: {e}")

def index_article(article):
    delete_article_chunks(article.id)
    texts, metadatas = build_chunks(article)
    if not texts:
        return 0

    vectorstore = get_vectorstore()
    ids = [f"article_{article.id}_chunk_{i}" for i in range(len(texts))]
    vectorstore.add_texts(
        texts=texts,
        metadatas=metadatas,
        ids=ids,
    )
    return len(ids)

def index_all_articles():
    articles = Article.objects.filter(status='published')
    total = 0
    for article in articles.iterator():
        total += index_article(article)
    logger.info(f"Indexed {total} chunks from {articles.count()} articles.")
    return total