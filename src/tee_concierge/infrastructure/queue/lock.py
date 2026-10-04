from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from redis.asyncio import Redis


class RedisConversationLock:
    def __init__(self, redis: "Redis", timeout: float = 30.0, wait: float = 30.0) -> None:
        self._redis = redis
        self._timeout = timeout
        self._wait = wait

    @asynccontextmanager
    async def hold(self, key: str) -> AsyncIterator[None]:
        lock = self._redis.lock(
            f"lock:conversation:{key}", timeout=self._timeout, blocking_timeout=self._wait
        )
        async with lock:
            yield
