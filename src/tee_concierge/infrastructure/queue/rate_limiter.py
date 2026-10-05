from redis.asyncio import Redis


class RedisRateLimiter:
    """Fixed-window counter per key (here: per customer phone)."""

    def __init__(self, redis: "Redis", limit: int, window_seconds: int = 60) -> None:
        self._redis = redis
        self._limit = limit
        self._window = window_seconds

    async def allow(self, key: str) -> bool:
        name = f"ratelimit:{key}"
        # Create the key with its TTL first, so a crash can never leave a counter
        # without an expiry (which would block that customer forever).
        await self._redis.set(name, 0, ex=self._window, nx=True)
        count = await self._redis.incr(name)
        return int(count) <= self._limit
