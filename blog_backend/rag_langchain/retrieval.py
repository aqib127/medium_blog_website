import logging
from django.conf import settings
from .vectorstore import get_vectorstore

logger = logging.getLogger(__name__)

def retrieve(query, limit=None):
    limit = limit or settings.RAG_TOP_K
    logger.info(f"Retrieving for query: '{query}'")
    vectorstore = get_vectorstore()
    docs_with_score = vectorstore.similarity_search_with_score(query, k=limit)
    logger.info(f"Retrieved {len(docs_with_score)} documents")
    results = []
    for doc, distance in docs_with_score:
        similarity = 1 - distance
        logger.info(f"  Score: {similarity:.4f} | Title: {doc.metadata.get('title', 'Unknown')}")
        if similarity >= settings.RAG_MIN_SIMILARITY:
            results.append({
                'content': doc.page_content,
                'metadata': doc.metadata,
                'score': round(similarity, 4),
            })
    logger.info(f"Filtered to {len(results)} documents above threshold {settings.RAG_MIN_SIMILARITY}")
    return results