"""Keep the vector store in sync with published articles.

Every publish/edit re-embeds the article and upserts its chunks; unpublishing
or deleting removes them. Each handler is wrapped so a down Ollama server or
missing Chroma data never breaks a normal article save.
"""
import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from articles.models import Article

from .indexing import index_article, delete_article_chunks

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Article)
def sync_article(sender, instance, **kwargs):
    try:
        if instance.status == Article.Status.PUBLISHED:
            index_article(instance)
        else:
            delete_article_chunks(instance.id)
    except Exception as exc:  # noqa: BLE001 — never break a save
        logger.warning('RAG sync failed for article %s: %s', instance.id, exc)


@receiver(post_delete, sender=Article)
def remove_article(sender, instance, **kwargs):
    try:
        delete_article_chunks(instance.id)
    except Exception as exc:  # noqa: BLE001
        logger.warning('RAG delete failed for article %s: %s', instance.id, exc)
