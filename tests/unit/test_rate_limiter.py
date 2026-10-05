from typing import Any

from tee_concierge.infrastructure.queue.rate_limiter import RedisRateLimiter


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    async def set(self, name: str, value: int, ex: int, nx: bool) -> None:
        if not (nx and name in self.values):
            self.values[name] = value
            self.ttls[name] = ex

    async def incr(self, name: str) -> int:
        self.values[name] += 1
        return self.values[name]


async def test_allows_up_to_the_limit_then_blocks_per_key() -> None:
    redis: Any = FakeRedis()
    limiter = RedisRateLimiter(redis, limit=3, window_seconds=60)

    first = [await limiter.allow("51911111111") for _ in range(5)]
    other = await limiter.allow("51922222222")

    assert first == [True, True, True, False, False]
    assert other is True


async def test_counter_always_has_a_ttl() -> None:
    redis = FakeRedis()
    await RedisRateLimiter(redis, limit=1, window_seconds=60).allow("k")  # type: ignore[arg-type]
    assert redis.ttls["ratelimit:k"] == 60
