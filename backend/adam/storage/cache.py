"""
[PHASE3] Redis cache layer for Adam Prism.
Provides a drop-in replacement for the in-memory TTLCache that works
across multiple workers/processes. Falls back to in-memory if Redis unavailable.

Usage:
    from adam.storage.cache import CacheClient
    cache = CacheClient()
    await cache.set("key", "value", ttl=300)
    value = await cache.get("key")
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger("adam_prism.cache")


class _InMemoryCache:
    """Fallback in-memory cache (single-process only)"""

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float]] = {}

    async def get(self, key: str) -> Optional[Any]:
        if key not in self._data:
            return None
        value, expires_at = self._data[key]
        if expires_at and time.time() > expires_at:
            del self._data[key]
            return None
        return value

    async def set(self, key: str, value: Any, ttl: float = 300.0) -> None:
        expires_at = time.time() + ttl if ttl > 0 else 0
        self._data[key] = (value, expires_at)

    async def delete(self, key: str) -> None:
        self._data.pop(key, None)

    async def clear(self) -> None:
        self._data.clear()

    async def stats(self) -> dict[str, int]:
        return {"size": len(self._data), "type": "memory"}


class _RedisCache:
    """Redis-backed cache (multi-process)"""

    def __init__(self, client) -> None:
        self._client = client

    async def get(self, key: str) -> Optional[Any]:
        try:
            raw = await self._client.get(key)
        except Exception as e:
            logger.warning(f"Redis GET failed: {e}")
            return None
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return raw

    async def set(self, key: str, value: Any, ttl: float = 300.0) -> None:
        try:
            payload = json.dumps(value)
            if ttl > 0:
                await self._client.set(key, payload, ex=int(ttl))
            else:
                await self._client.set(key, payload)
        except Exception as e:
            logger.warning(f"Redis SET failed: {e}")

    async def delete(self, key: str) -> None:
        try:
            await self._client.delete(key)
        except Exception as e:
            logger.warning(f"Redis DELETE failed: {e}")

    async def clear(self) -> None:
        try:
            await self._client.flushdb()
        except Exception as e:
            logger.warning(f"Redis FLUSHDB failed: {e}")

    async def stats(self) -> dict[str, int]:
        try:
            info = await self._client.info("keyspace")
            return {"size": info.get("db0", 0).get("keys", 0) if isinstance(info.get("db0"), dict) else 0, "type": "redis"}
        except Exception:
            return {"size": 0, "type": "redis"}


class CacheClient:
    """[PHASE3] Unified cache client. Uses Redis if available, else in-memory."""

    def __init__(self, redis_url: str | None = None) -> None:
        self._impl: Any = None
        self._redis_url = redis_url or os.environ.get("ADAM_REDIS_URL", "").strip()
        self._enabled = bool(self._redis_url)
        self._lock = asyncio.Lock()

    async def _ensure_init(self) -> None:
        if self._impl is not None:
            return
        async with self._lock:
            if self._impl is not None:
                return
            if self._enabled:
                try:
                    import redis.asyncio as redis
                    client = redis.from_url(
                        self._redis_url,
                        encoding="utf-8",
                        decode_responses=True,
                        socket_connect_timeout=3.0,
                        socket_timeout=5.0,
                    )
                    # Test connection
                    await client.ping()
                    self._impl = _RedisCache(client)
                    logger.info(f"Redis cache enabled: {self._redis_url.split('@')[-1]}")
                    return
                except Exception as e:
                    logger.warning(f"Redis unavailable, falling back to in-memory: {e}")
            self._impl = _InMemoryCache()
            logger.info("Using in-memory cache (single-process only)")

    async def get(self, key: str) -> Optional[Any]:
        await self._ensure_init()
        return await self._impl.get(key)

    async def set(self, key: str, value: Any, ttl: float = 300.0) -> None:
        await self._ensure_init()
        await self._impl.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        await self._ensure_init()
        await self._impl.delete(key)

    async def clear(self) -> None:
        await self._ensure_init()
        await self._impl.clear()

    async def stats(self) -> dict[str, Any]:
        await self._ensure_init()
        return await self._impl.stats()

    # ── Decorator helper ────────────────────────────────────────

    def cached(self, ttl: float = 300.0, key_prefix: str = ""):
        """[PHASE3] Decorator for caching async function results."""
        def decorator(func):
            async def wrapper(*args, **kwargs):
                # Build cache key from function name + args
                key_parts = [key_prefix or func.__name__]
                key_parts.extend(str(a) for a in args)
                key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = ":".join(key_parts)
                # Try cache first
                cached_val = await self.get(cache_key)
                if cached_val is not None:
                    return cached_val
                # Call function
                result = await func(*args, **kwargs)
                # Store in cache
                await self.set(cache_key, result, ttl)
                return result
            return wrapper
        return decorator
