"""
newsletter/models.py

Permanent storage for newsletter subscribers.
Redis handles temporary state (tokens, queue, rate limits).
"""

import uuid
from django.db import models
from django.utils import timezone
from core.models import BaseModel


class NewsletterSubscriber(BaseModel):
    """Permanent subscriber record."""

    email = models.EmailField(unique=True, db_index=True)
    name = models.CharField(max_length=150, blank=True, default='')
    is_confirmed = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)

    confirmed_at = models.DateTimeField(null=True, blank=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)
    last_email_sent_at = models.DateTimeField(null=True, blank=True)

    source = models.CharField(max_length=50, blank=True, default='website')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_confirmed', 'is_active']),
        ]

    def __str__(self):
        status = 'confirmed' if self.is_confirmed else 'pending'
        return f"{self.email} ({status})"

    def confirm(self):
        self.is_confirmed = True
        self.is_active = True
        self.confirmed_at = timezone.now()
        self.save(update_fields=['is_confirmed', 'is_active', 'confirmed_at'])

    def unsubscribe(self):
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=['is_active', 'unsubscribed_at'])


class NewsletterSendLog(BaseModel):
    """Log of newsletter sends for tracking & analytics."""

    subject = models.CharField(max_length=300)
    body_preview = models.TextField(blank=True, default='')
    sent_to_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    sent_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newsletter_sends',
    )
    article = models.ForeignKey(
        'articles.Article',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='newsletter_sends',
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ('queued', 'Queued'),
            ('sending', 'Sending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='queued',
    )
    error_message = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} -> {self.sent_to_count} subscribers"
