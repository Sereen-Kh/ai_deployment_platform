"""Shared Redis client for caching and rate limiting."""

import json
from typing import Optional, Any
from redis import asyncio as aioredis
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    """Async Redis client wrapper."""

    def __init__(self, url: str):
        """Initialize Redis client.

        Args:
            url: Redis connection URL
        """
        self.url = url
        self.redis: Optional[aioredis.Redis] = None

    async def connect(self):
        """Connect to Redis."""
        self.redis = await aioredis.from_url(
            self.url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info("Connected to Redis")

    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            logger.info("Disconnected from Redis")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Optional[Any]: Cached value or None
        """
        if not self.redis:
            return None

        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis GET error: {e}")
            return None

    async def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration time in seconds

        Returns:
            bool: True if successful
        """
        if not self.redis:
            return False

        try:
            serialized = json.dumps(value)
            await self.redis.set(key, serialized, ex=expire)
            return True
        except Exception as e:
            logger.error(f"Redis SET error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache.

        Args:
            key: Cache key

        Returns:
            bool: True if successful
        """
        if not self.redis:
            return False

        try:
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis DELETE error: {e}")
            return False

    async def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment counter.

        Args:
            key: Counter key
            amount: Increment amount

        Returns:
            Optional[int]: New counter value
        """
        if not self.redis:
            return None

        try:
            return await self.redis.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR error: {e}")
            return None

    async def rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, int]:
        """Check rate limit.

        Args:
            key: Rate limit key
            limit: Maximum requests
            window: Time window in seconds

        Returns:
            tuple[bool, int]: (allowed, remaining)
        """
        if not self.redis:
            return True, limit

        try:
            current = await self.redis.get(key)
            if current is None:
                await self.redis.setex(key, window, 1)
                return True, limit - 1

            count = int(current)
            if count >= limit:
                return False, 0

            await self.redis.incr(key)
            return True, limit - count - 1
        except Exception as e:
            logger.error(f"Redis rate limit error: {e}")
            return True, limit
