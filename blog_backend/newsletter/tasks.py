"""
newsletter/tasks.py

Background tasks for newsletter.
"""

import logging
from django.utils import timezone
from .models import NewsletterSubscriber
from .emails import send_article_newsletter

logger = logging.getLogger(__name__)


def send_article_to_all_subscribers(article, batch_size: int = 50) -> dict:
    subscribers = NewsletterSubscriber.objects.filter(
        is_confirmed=True,
        is_active=True,
    )

    sent = 0
    failed = 0

    for subscriber in subscribers.iterator(chunk_size=batch_size):
        try:
            ok = send_article_newsletter(subscriber, article)
            if ok:
                subscriber.last_email_sent_at = timezone.now()
                subscriber.save(update_fields=['last_email_sent_at'])
                sent += 1
            else:
                failed += 1
        except Exception as e:
            logger.exception(f"Failed to send to {subscriber.email}: {e}")
            failed += 1

    logger.info(f"Article newsletter sent: {sent} success, {failed} failed")
    return {"sent": sent, "failed": failed}
