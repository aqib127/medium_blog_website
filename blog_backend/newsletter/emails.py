"""
newsletter/emails.py

Email sending helpers.
"""

import logging
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

logger = logging.getLogger(__name__)


def _frontend_url(path: str = '') -> str:
    base = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
    path = path.lstrip('/')
    return f"{base}/{path}" if path else base


def send_confirmation_email(subscriber, token: str) -> bool:
    try:
        confirm_url = _frontend_url(f"newsletter/confirm?token={token}")
        subject = "Confirm your newsletter subscription"

        text_body = (
            f"Hi {subscriber.name or 'there'},\n\n"
            f"Thanks for subscribing!\n\n"
            f"Confirm your subscription: {confirm_url}\n\n"
            f"This link expires in 1 hour.\n"
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #1F4E4A; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">Confirm Subscription</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
                <p>Hi {subscriber.name or 'there'},</p>
                <p>Thanks for subscribing to our newsletter!</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{confirm_url}"
                       style="background: #1F4E4A; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 6px; font-weight: 600;">
                        Confirm Subscription
                    </a>
                </p>
                <p style="color: #888; font-size: 13px;">
                    This link expires in 1 hour.
                </p>
            </div>
        </body>
        </html>
        """

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            to=[subscriber.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        logger.info(f"Confirmation email sent to {subscriber.email}")
        return True
    except Exception as e:
        logger.exception(f"Failed to send confirmation email: {e}")
        return False


def send_welcome_email(subscriber) -> bool:
    try:
        unsubscribe_url = _frontend_url(f"newsletter/unsubscribe?token={subscriber.unsubscribe_token}")
        subject = "Welcome to our newsletter!"

        text_body = (
            f"Hi {subscriber.name or 'there'},\n\n"
            f"Your subscription is confirmed!\n\n"
            f"Unsubscribe: {unsubscribe_url}\n"
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #1F4E4A; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">Welcome!</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
                <p>Hi {subscriber.name or 'there'},</p>
                <p>Your subscription is <strong>confirmed</strong>!</p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #888; font-size: 12px;">
                    <a href="{unsubscribe_url}" style="color: #888;">Unsubscribe</a>
                </p>
            </div>
        </body>
        </html>
        """

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            to=[subscriber.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)

        logger.info(f"Welcome email sent to {subscriber.email}")
        return True
    except Exception as e:
        logger.exception(f"Failed to send welcome email: {e}")
        return False


def send_article_newsletter(subscriber, article) -> bool:
    try:
        article_url = _frontend_url(f"article/{article.id}")
        unsubscribe_url = _frontend_url(f"newsletter/unsubscribe?token={subscriber.unsubscribe_token}")

        subject = f"New article: {article.title}"

        text_body = (
            f"Hi {subscriber.name or 'there'},\n\n"
            f"New article: {article.title}\n"
            f"by {article.author.name}\n\n"
            f"Read: {article_url}\n\n"
            f"Unsubscribe: {unsubscribe_url}\n"
        )

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: #1F4E4A; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 22px;">New Article</h1>
            </div>
            <div style="background: #f9f9f9; padding: 30px; border-radius: 0 0 8px 8px;">
                <h2 style="margin-top: 0;">{article.title}</h2>
                <p style="color: #666;">by {article.author.name}</p>
                <p>{article.dek or ''}</p>
                <p style="text-align: center; margin: 30px 0;">
                    <a href="{article_url}"
                       style="background: #1F4E4A; color: white; padding: 12px 30px;
                              text-decoration: none; border-radius: 6px; font-weight: 600;">
                        Read Article
                    </a>
                </p>
                <hr style="border: none; border-top: 1px solid #ddd; margin: 30px 0;">
                <p style="color: #888; font-size: 12px;">
                    <a href="{unsubscribe_url}" style="color: #888;">Unsubscribe</a>
                </p>
            </div>
        </body>
        </html>
        """

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com'),
            to=[subscriber.email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send(fail_silently=False)
        return True
    except Exception as e:
        logger.exception(f"Failed to send article newsletter: {e}")
        return False
