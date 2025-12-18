"""Redis connection and utilities."""

import json
from typing import Any, Optional

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from .config import settings

# Connection pool
pool: Optional[ConnectionPool] = None


async def get_redis_pool() -> ConnectionPool:
    """Get or create Redis connection pool."""
    global pool
    if pool is None:
        pool = ConnectionPool.from_url(
            settings.redis_url,
            max_connections=20,
            decode_responses=True,
        )
    return pool


async def get_redis() -> redis.Redis:
    """Get Redis connection from pool."""
    return redis.Redis(connection_pool=await get_redis_pool())


async def close_redis() -> None:
    """Close Redis connection pool."""
    global pool
    if pool is not None:
        await pool.disconnect()
        pool = None


class RedisCache:
    """Redis cache utility class."""

    def __init__(self, prefix: str = "cache"):
        self.prefix = prefix

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key."""
        return f"{self.prefix}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = await get_redis()
        value = await client.get(self._make_key(key))
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """Set value in cache with optional TTL."""
        client = await get_redis()
        ttl = ttl or settings.redis_cache_ttl

        if isinstance(value, (dict, list)):
            value = json.dumps(value)

        return await client.set(self._make_key(key), value, ex=ttl)

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        client = await get_redis()
        return bool(await client.delete(self._make_key(key)))

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        client = await get_redis()
        return bool(await client.exists(self._make_key(key)))

    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter."""
        client = await get_redis()
        return await client.incrby(self._make_key(key), amount)

    async def expire(self, key: str, ttl: int) -> bool:
        """Set expiration on key."""
        client = await get_redis()
        return await client.expire(self._make_key(key), ttl)


class RateLimiter:
    """Rate limiter using Redis."""

    def __init__(
        self,
        requests: int = settings.rate_limit_requests,
        period: int = settings.rate_limit_period,
    ):
        self.requests = requests
        self.period = period
        self.cache = RedisCache(prefix="ratelimit")

    async def is_allowed(self, identifier: str) -> tuple[bool, int]:
        """
        Check if request is allowed under rate limit.
        Returns (allowed, remaining_requests).
        """
        client = await get_redis()
        key = f"ratelimit:{identifier}"

        current = await client.get(key)

        if current is None:
            await client.set(key, 1, ex=self.period)
            return True, self.requests - 1

        current_count = int(current)
        if current_count >= self.requests:
            ttl = await client.ttl(key)
            return False, 0

        await client.incr(key)
        return True, self.requests - current_count - 1

    async def reset(self, identifier: str) -> bool:
        """Reset rate limit for identifier."""
        client = await get_redis()
        return bool(await client.delete(f"ratelimit:{identifier}"))


# Default instances
cache = RedisCache()
rate_limiter = RateLimiter()
