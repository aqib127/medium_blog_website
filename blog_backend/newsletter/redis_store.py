"""
newsletter/redis_store.py

All Redis operations for newsletter functionality.
Uses django_redis connection (Azure Managed Redis compatible).
"""

import json
import logging
import secrets
from typing import Optional

from django_redis import get_redis_connection

logger = logging.getLogger(__name__)


CONFIRM_KEY = "newsletter:confirm:{token}"
RATE_KEY = "newsletter:rate:{ip}"
QUEUE_KEY = "newsletter:queue"
STATS_TOTAL = "newsletter:stats:total"
STATS_CONFIRMED = "newsletter:stats:confirmed"

CONFIRM_TTL = 3600
RATE_TTL = 60
RATE_LIMIT = 5


def _redis():
    return get_redis_connection("default")


def create_confirmation_token(email: str, ttl: int = CONFIRM_TTL) -> str:
    token = secrets.token_urlsafe(32)
    key = CONFIRM_KEY.format(token=token)
    r = _redis()
    r.setex(key, ttl, email)
    logger.info(f"Confirmation token created for {email}")
    return token


def consume_confirmation_token(token: str) -> Optional[str]:
    key = CONFIRM_KEY.format(token=token)
    r = _redis()
    email = r.get(key)
    if email is None:
        return None
    r.delete(key)
    return email.decode() if isinstance(email, bytes) else email


def peek_confirmation_token(token: str) -> Optional[str]:
    key = CONFIRM_KEY.format(token=token)
    r = _redis()
    email = r.get(key)
    return email.decode() if isinstance(email, bytes) else email


def check_rate_limit(ip: str):
    if not ip:
        return True, RATE_LIMIT
    key = RATE_KEY.format(ip=ip)
    r = _redis()
    try:
        count = r.incr(key)
        if count == 1:
            r.expire(key, RATE_TTL)
        remaining = max(0, RATE_LIMIT - count)
        return count <= RATE_LIMIT, remaining
    except Exception as e:
        logger.exception(f"Rate limit check failed: {e}")
        return True, RATE_LIMIT


def increment_total_subs():
    try:
        _redis().incr(STATS_TOTAL)
    except Exception as e:
        logger.warning(f"Failed to increment total: {e}")


def increment_confirmed_subs():
    try:
        _redis().incr(STATS_CONFIRMED)
    except Exception as e:
        logger.warning(f"Failed to increment confirmed: {e}")


def get_stats() -> dict:
    try:
        r = _redis()
        return {
            "total_subscriptions": int(r.get(STATS_TOTAL) or 0),
            "total_confirmed": int(r.get(STATS_CONFIRMED) or 0),
        }
    except Exception as e:
        logger.warning(f"Stats fetch failed: {e}")
        return {"total_subscriptions": 0, "total_confirmed": 0}


def enqueue_email(payload: dict):
    r = _redis()
    r.lpush(QUEUE_KEY, json.dumps(payload))


def dequeue_email() -> Optional[dict]:
    r = _redis()
    raw = r.rpop(QUEUE_KEY)
    if raw is None:
        return None
    return json.loads(raw)


def queue_size() -> int:
    try:
        return _redis().llen(QUEUE_KEY)
    except Exception:
        return 0


def health_check() -> bool:
    try:
        return bool(_redis().ping())
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
