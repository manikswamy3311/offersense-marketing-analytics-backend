import redis
import json
import os
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

_client = None


def _get_client():
    """Lazy Redis connection — returns None if Redis is unavailable."""
    global _client
    if _client is None:
        try:
            r = redis.from_url(REDIS_URL, decode_responses=True, socket_connect_timeout=1)
            r.ping()
            _client = r
            logger.info("Redis cache connected")
        except Exception:
            logger.warning("Redis not available — caching disabled")
    return _client


def cache_get(key: str):
    """Return cached value or None on miss / error."""
    try:
        r = _get_client()
        if r is None:
            return None
        val = r.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def cache_set(key: str, value, ttl: int = 60):
    """Store value in cache with TTL (seconds). Silent on error."""
    try:
        r = _get_client()
        if r is None:
            return
        r.setex(key, ttl, json.dumps(value))
    except Exception:
        pass


def cache_delete(*keys: str):
    """Delete one or more cache keys. Silent on error."""
    try:
        r = _get_client()
        if r is None:
            return
        r.delete(*keys)
    except Exception:
        pass


def invalidate_analytics_cache():
    """Bust all analytics and KPI cache keys after a campaign write."""
    cache_delete("kpis", "analytics:summary", "analytics:benchmark", "analytics:scores")
