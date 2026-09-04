"""Rate limiting and abuse prevention utilities for Decisera API."""

from datetime import datetime, timezone
import logging
from typing import Tuple, Optional, Dict, Any
from slowapi import Limiter
from slowapi.util import get_remote_address
from .config import settings
from .cache import get_redis_client

logger = logging.getLogger(__name__)

# Shared SlowAPI Limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    enabled=settings.rate_limit_enabled,
)

# In-memory quota store for daily cap fallback when Redis is absent
_daily_quota_store: Dict[str, Dict[str, int]] = {}


def check_and_increment_daily_copilot_quota(
    identifier: str = "system",
    limit: Optional[int] = None,
) -> Tuple[bool, int, int]:
    """
    Check and increment daily call count for Copilot queries.
    Enforces a hard 24-hour cap across the system or per-identifier to prevent
    LLM API key exhaustion and financial/resource abuse.

    Args:
        identifier: Tracking identifier ('system' or client IP)
        limit: Maximum allowed calls per day (defaults to settings.copilot_daily_limit)

    Returns:
        Tuple[bool, int, int]: (allowed, current_count, max_limit)
    """
    max_limit = limit if limit is not None else settings.copilot_daily_limit
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    redis_key = f"copilot:quota:{today}:{identifier}"

    # 1. Try Redis for distributed persistence across container instances
    client = get_redis_client()
    if client is not None:
        try:
            count = client.incr(redis_key)
            if count == 1:
                # 24 hours + 1 hour buffer (90000 seconds) TTL
                client.expire(redis_key, 90000)
            if count > max_limit:
                logger.warning(
                    f"Daily Copilot quota exceeded for '{identifier}': {count}/{max_limit}"
                )
                return False, count, max_limit
            return True, count, max_limit
        except Exception as e:
            logger.warning(
                f"Redis quota check failed ({e}); falling back to in-memory tracking."
            )

    # 2. In-memory fallback if Redis is unavailable or fails
    day_store = _daily_quota_store.setdefault(today, {})
    current = day_store.get(identifier, 0) + 1
    day_store[identifier] = current

    # Prune past dates to prevent memory leak
    for past_day in list(_daily_quota_store.keys()):
        if past_day != today:
            del _daily_quota_store[past_day]

    if current > max_limit:
        logger.warning(
            f"Daily Copilot quota exceeded (in-memory) for '{identifier}': {current}/{max_limit}"
        )
        return False, current, max_limit

    return True, current, max_limit


def get_daily_copilot_quota_status(
    identifier: str = "system",
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """Get current quota usage stats without incrementing."""
    max_limit = limit if limit is not None else settings.copilot_daily_limit
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    redis_key = f"copilot:quota:{today}:{identifier}"

    client = get_redis_client()
    if client is not None:
        try:
            val = client.get(redis_key)
            count = int(val) if val else 0
            return {
                "date": today,
                "used": count,
                "limit": max_limit,
                "remaining": max(0, max_limit - count),
            }
        except Exception:
            pass

    count = _daily_quota_store.get(today, {}).get(identifier, 0)
    return {
        "date": today,
        "used": count,
        "limit": max_limit,
        "remaining": max(0, max_limit - count),
    }


def reset_daily_copilot_quota(identifier: Optional[str] = None) -> None:
    """Reset daily quota count (primarily for testing)."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if identifier:
        if today in _daily_quota_store and identifier in _daily_quota_store[today]:
            del _daily_quota_store[today][identifier]
        client = get_redis_client()
        if client is not None:
            try:
                client.delete(f"copilot:quota:{today}:{identifier}")
            except Exception:
                pass
    else:
        _daily_quota_store.clear()
        client = get_redis_client()
        if client is not None:
            try:
                keys = client.keys(f"copilot:quota:{today}:*")
                if keys:
                    client.delete(*keys)
            except Exception:
                pass
