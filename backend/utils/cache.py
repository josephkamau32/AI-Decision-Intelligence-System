import redis
from typing import Any, Optional
import json
import logging
from functools import wraps
from ..utils.config import settings

logger = logging.getLogger(__name__)

# Redis client instance
redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """Get or create Redis client."""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.from_url(
                settings.redis_url, decode_responses=True, socket_connect_timeout=5
            )
            # Test connection
            redis_client.ping()
            logger.info("Redis connection established")
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            redis_client = None
    return redis_client


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key from prefix and arguments."""
    key_parts = [prefix]
    key_parts.extend(str(arg) for arg in args)
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)


def cache_get(key: str) -> Optional[Any]:
    """Get value from cache."""
    if not settings.cache_enabled:
        return None

    client = get_redis_client()
    if client is None:
        return None

    try:
        value = client.get(key)
        if value:
            return json.loads(value)
    except (redis.RedisError, json.JSONDecodeError) as e:
        logger.error(f"Cache get error for key {key}: {e}")
    return None


def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in cache with optional TTL."""
    if not settings.cache_enabled:
        return False

    client = get_redis_client()
    if client is None:
        return False

    try:
        serialized = json.dumps(value)
        if ttl:
            client.setex(key, ttl, serialized)
        else:
            client.setex(key, settings.cache_ttl, serialized)
        return True
    except (redis.RedisError, TypeError) as e:
        logger.error(f"Cache set error for key {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    """Delete value from cache."""
    if not settings.cache_enabled:
        return False

    client = get_redis_client()
    if client is None:
        return False

    try:
        client.delete(key)
        return True
    except redis.RedisError as e:
        logger.error(f"Cache delete error for key {key}: {e}")
        return False


def cache_clear_pattern(pattern: str) -> int:
    """Clear all cache keys matching pattern."""
    if not settings.cache_enabled:
        return 0

    client = get_redis_client()
    if client is None:
        return 0

    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except redis.RedisError as e:
        logger.error(f"Cache clear pattern error for {pattern}: {e}")
        return 0


def cached(prefix: str, ttl: Optional[int] = None):
    """Decorator to cache function results."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = cache_get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for key: {key}")
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            cache_set(key, result, ttl)
            logger.debug(f"Cache miss, stored result for key: {key}")

            return result

        return wrapper

    return decorator
