import hashlib
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

KEY_PREFIX = "ratelimit:v1"


@dataclass(frozen=True)
class RateLimitRule:
    name: str
    limit: int
    window_seconds: int


class RateLimitExceededError(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__(f"Retry after {retry_after_seconds}s")
        self.retry_after_seconds = retry_after_seconds


class CounterStore(Protocol):
    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]: ...


class RedisCounterStore:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        async with self._redis.pipeline(transaction=True) as pipeline:
            pipeline.incr(key)
            pipeline.expire(key, window_seconds, nx=True)
            pipeline.ttl(key)
            count, _, ttl = await pipeline.execute()
        return int(count), max(int(ttl), 1)


def _client_key(rule: RateLimitRule, client_id: str) -> str:
    client_hash = hashlib.sha256(client_id.encode()).hexdigest()
    return f"{KEY_PREFIX}:{rule.name}:{client_hash}"


def _shared_key(rule: RateLimitRule) -> str:
    return f"{KEY_PREFIX}:{rule.name}"


class RateLimiter:
    def __init__(self, store: CounterStore) -> None:
        self._store = store

    async def enforce(
        self,
        client_id: str,
        client_rules: Sequence[RateLimitRule],
        shared_rules: Sequence[RateLimitRule] = (),
    ) -> None:
        try:
            await self._enforce_each(client_rules, lambda rule: _client_key(rule, client_id))
            await self._enforce_each(shared_rules, _shared_key)
        except RedisError:
            logger.warning("Rate limit store unavailable, allowing request", exc_info=True)

    async def _enforce_each(
        self, rules: Sequence[RateLimitRule], key_for: Callable[[RateLimitRule], str]
    ) -> None:
        retry_after: list[int] = []
        for rule in rules:
            count, ttl = await self._store.increment(key_for(rule), rule.window_seconds)
            if count > rule.limit:
                retry_after.append(ttl)
        if retry_after:
            raise RateLimitExceededError(max(retry_after))
