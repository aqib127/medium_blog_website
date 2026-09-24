"""
newsletter/tasks.py

Background tasks for newsletter.
Supports both sync (API calls) and async (Celery) execution.
"""

import logging
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from .models import NewsletterSubscriber, NewsletterSendLog
from .emails import send_article_newsletter

logger = logging.getLogger(__name__)


# ============================================================
# SYNCHRONOUS (for immediate API calls)
# ============================================================

def send_article_to_all_subscribers(article, batch_size=50):
    """Send article to all confirmed subscribers (synchronous)."""
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


# ============================================================
# CELERY ASYNC TASKS (scheduled via Beat)
# ============================================================

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_daily_digest_task(self, hours=24, limit=5):
    """
    Send daily digest of top articles to all subscribers.
    Scheduled: 9 AM UTC daily.
    """
    from articles.models import Article

    since = timezone.now() - timedelta(hours=hours)

    articles = list(
        Article.objects.filter(
            status='published',
            published_at__gte=since,
        ).order_by('-claps_count')[:limit]
    )

    if not articles:
        logger.info("No articles for daily digest.")
        return {"sent": 0, "failed": 0, "articles": 0}

    # Log the send
    log = NewsletterSendLog.objects.create(
        subject=f"Daily Digest — {len(articles)} articles",
        body_preview=f"Top {len(articles)} articles from last {hours}h",
        status='sending',
    )

    # Send to all subscribers
    subscribers = NewsletterSubscriber.objects.filter(
        is_confirmed=True,
        is_active=True,
    )

    sent = 0
    failed = 0

    for subscriber in subscribers.iterator(chunk_size=50):
        try:
            for article in articles:
                ok = send_article_newsletter(subscriber, article)
                if ok:
                    sent += 1
                else:
                    failed += 1
        except Exception as e:
            logger.exception(f"Failed for {subscriber.email}: {e}")
            failed += 1

    # Update log
    log.sent_to_count = sent
    log.failed_count = failed
    log.status = 'completed' if failed == 0 else 'failed'
    log.save()

    logger.info(f"Daily digest: {sent} sent, {failed} failed")
    return {"sent": sent, "failed": failed, "articles": len(articles)}


@shared_task
def cleanup_send_logs_task(days=90):
    """Delete send logs older than N days. Scheduled: 3 AM UTC daily."""
    cutoff = timezone.now() - timedelta(days=days)

    deleted, _ = NewsletterSendLog.objects.filter(
        created_at__lt=cutoff
    ).delete()

    logger.info(f"Cleaned up {deleted} old send logs")
    return {"deleted": deleted}


@shared_task
def cleanup_expired_tokens_task():
    """Cleanup orphaned tokens from Redis. Scheduled: every 30 min."""
    from . import redis_store

    try:
        r = redis_store._redis()
        keys = r.keys('newsletter:confirm:*')

        # TTL keys are auto-deleted by Redis, so this is a safety net
        logger.info(f"Token check: {len(keys)} active tokens")
        return {"active_tokens": len(keys)}
    except Exception as e:
        logger.exception(f"Token cleanup failed: {e}")
        return {"error": str(e)}


@shared_task(bind=True, max_retries=3)
def retry_failed_sends_task(self):
    """Retry failed sends from last 24h. Scheduled: hourly."""
    since = timezone.now() - timedelta(hours=24)

    failed_logs = NewsletterSendLog.objects.filter(
        status='failed',
        created_at__gte=since,
    ).order_by('-created_at')[:10]

    retried = 0
    for log in failed_logs:
        try:
            if log.article:
                result = send_article_to_all_subscribers(log.article)
                retried += 1
                logger.info(f"Retried log {log.id}: {result}")
        except Exception as e:
            logger.exception(f"Retry failed for log {log.id}: {e}")

    return {"retried": retried}


@shared_task
def send_test_email_task(email):
    """Send test email — used for verification."""
    from django.core.mail import send_mail
    from django.conf import settings

    send_mail(
        subject='Celery Test — Medium Blog',
        message='This is a test email from Celery task.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    return {"sent_to": email}
