"""
newsletter/views.py

API endpoints for newsletter subscription.
"""

import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import NewsletterSubscriber, NewsletterSendLog
from .serializers import (
    SubscribeSerializer,
    ConfirmSerializer,
    UnsubscribeSerializer,
)
from . import redis_store
from .emails import send_confirmation_email, send_welcome_email
from .tasks import send_article_to_all_subscribers

logger = logging.getLogger(__name__)


def _get_client_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


@api_view(['POST'])
@permission_classes([AllowAny])
def subscribe(request):
    serializer = SubscribeSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email'].lower().strip()
    name = serializer.validated_data.get('name', '').strip()
    source = serializer.validated_data.get('source', 'website')
    ip = _get_client_ip(request) or None  # GenericIPAddressField needs None for empty

    allowed, remaining = redis_store.check_rate_limit(ip)
    if not allowed:
        return Response(
            {"error": "Too many requests. Please try again later."},
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    subscriber, created = NewsletterSubscriber.objects.get_or_create(
        email=email,
        defaults={
            'name': name,
            'source': source,
            'ip_address': ip,
        },
    )

    if not created and subscriber.is_confirmed and subscriber.is_active:
        return Response({
            "success": True,
            "message": "You're already subscribed!",
            "already_subscribed": True,
        })

    if not created and not subscriber.is_active:
        subscriber.is_active = True
        subscriber.is_confirmed = False
        subscriber.unsubscribed_at = None
        if name:
            subscriber.name = name
        subscriber.save()

    try:
        token = redis_store.create_confirmation_token(email)
        ok = send_confirmation_email(subscriber, token)
        if not ok:
            logger.warning(f"Failed to send confirmation email to {email}")
    except Exception as e:
        logger.exception(f"Subscribe failed: {e}")
        return Response(
            {"error": "Failed to send confirmation email. Please try again."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if created:
        redis_store.increment_total_subs()

    return Response({
        "success": True,
        "message": "Check your email to confirm your subscription.",
        "email": email,
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def confirm(request, token=None):
    if token is None and request.method == 'POST':
        serializer = ConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']

    if not token:
        return Response(
            {"error": "Token is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    email = redis_store.consume_confirmation_token(token)
    if not email:
        return Response({
            "success": False,
            "error": "Invalid or expired token. Please subscribe again.",
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        subscriber = NewsletterSubscriber.objects.get(email=email)
    except NewsletterSubscriber.DoesNotExist:
        return Response({
            "success": False,
            "error": "Subscriber not found.",
        }, status=status.HTTP_404_NOT_FOUND)

    if subscriber.is_confirmed:
        return Response({
            "success": True,
            "message": "Already confirmed.",
            "email": email,
        })

    subscriber.confirm()
    redis_store.increment_confirmed_subs()

    try:
        send_welcome_email(subscriber)
    except Exception as e:
        logger.warning(f"Welcome email failed: {e}")

    return Response({
        "success": True,
        "message": "Subscription confirmed! Welcome aboard.",
        "email": email,
    })


@api_view(['POST', 'GET'])
@permission_classes([AllowAny])
def unsubscribe(request, token=None):
    email = None

    if token:
        try:
            subscriber = NewsletterSubscriber.objects.get(unsubscribe_token=token)
            email = subscriber.email
        except NewsletterSubscriber.DoesNotExist:
            return Response({
                "success": False,
                "error": "Invalid unsubscribe link.",
            }, status=status.HTTP_400_BAD_REQUEST)
    else:
        serializer = UnsubscribeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')
        if not email:
            return Response(
                {"error": "Email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        email = email.lower().strip()

    try:
        subscriber = NewsletterSubscriber.objects.get(email=email)
    except NewsletterSubscriber.DoesNotExist:
        return Response({
            "success": True,
            "message": "You are not subscribed.",
        })

    if not subscriber.is_active:
        return Response({
            "success": True,
            "message": "Already unsubscribed.",
        })

    subscriber.unsubscribe()

    return Response({
        "success": True,
        "message": "You have been unsubscribed.",
        "email": email,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def status_view(request):
    email = request.query_params.get('email', '').lower().strip()
    if not email:
        return Response(
            {"error": "email query param required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        subscriber = NewsletterSubscriber.objects.get(email=email)
        return Response({
            "email": email,
            "subscribed": True,
            "confirmed": subscriber.is_confirmed,
            "active": subscriber.is_active,
        })
    except NewsletterSubscriber.DoesNotExist:
        return Response({
            "email": email,
            "subscribed": False,
            "confirmed": False,
            "active": False,
        })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def stats(request):
    db_stats = {
        "total_in_db": NewsletterSubscriber.objects.count(),
        "confirmed_in_db": NewsletterSubscriber.objects.filter(is_confirmed=True).count(),
        "active_in_db": NewsletterSubscriber.objects.filter(is_active=True).count(),
    }
    redis_stats = redis_store.get_stats()
    return Response({
        "database": db_stats,
        "redis": redis_stats,
        "queue_size": redis_store.queue_size(),
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_to_all(request):
    article_id = request.data.get('article_id')
    if not article_id:
        return Response(
            {"error": "article_id is required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from articles.models import Article
    try:
        article = Article.objects.get(id=article_id, status='published')
    except Article.DoesNotExist:
        return Response(
            {"error": f"Article {article_id} not found or not published."},
            status=status.HTTP_404_NOT_FOUND,
        )

    log = NewsletterSendLog.objects.create(
        subject=f"New article: {article.title}",
        body_preview=article.dek or '',
        sent_by=request.user,
        article=article,
        status='sending',
    )

    try:
        result = send_article_to_all_subscribers(article)
        log.sent_to_count = result['sent']
        log.failed_count = result['failed']
        log.status = 'completed'
        log.save()
        return Response({
            "success": True,
            "sent": result['sent'],
            "failed": result['failed'],
            "article_id": article.id,
            "article_title": article.title,
        })
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.save()
        logger.exception("Send to all failed")
        return Response(
            {"error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
