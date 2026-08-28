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
    except Exception as e:
        logger.warning(f"RAG sync failed for article {instance.id}: {e}")

@receiver(post_delete, sender=Article)
def remove_article(sender, instance, **kwargs):
    try:
        delete_article_chunks(instance.id)
    except Exception as e:
        logger.warning(f"RAG delete failed for article {instance.id}: {e}")
