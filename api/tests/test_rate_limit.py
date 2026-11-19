import pytest

from app.services.rate_limit import RateLimiter, RateLimitExceededError, RateLimitRule
from tests.fakes import InMemoryCounterStore, UnavailableCounterStore

BURST = RateLimitRule("burst", limit=2, window_seconds=600)
DAILY = RateLimitRule("daily", limit=3, window_seconds=86_400)
GLOBAL = RateLimitRule("global", limit=3, window_seconds=86_400)


async def test_allows_requests_up_to_the_limit() -> None:
    limiter = RateLimiter(InMemoryCounterStore())

    for _ in range(BURST.limit):
        await limiter.enforce("203.0.113.7", [BURST])


async def test_rejects_requests_over_the_limit_with_a_retry_delay() -> None:
    limiter = RateLimiter(InMemoryCounterStore())
    for _ in range(BURST.limit):
        await limiter.enforce("203.0.113.7", [BURST])

    with pytest.raises(RateLimitExceededError) as raised:
        await limiter.enforce("203.0.113.7", [BURST])

    assert raised.value.retry_after_seconds == BURST.window_seconds


async def test_reports_the_longest_wait_when_several_limits_are_hit() -> None:
    limiter = RateLimiter(InMemoryCounterStore())
    tight_daily = RateLimitRule("tight-daily", limit=2, window_seconds=86_400)
    for _ in range(BURST.limit):
        await limiter.enforce("203.0.113.7", [BURST, tight_daily])

    with pytest.raises(RateLimitExceededError) as raised:
        await limiter.enforce("203.0.113.7", [BURST, tight_daily])

    assert raised.value.retry_after_seconds == tight_daily.window_seconds


async def test_counts_each_client_separately() -> None:
    limiter = RateLimiter(InMemoryCounterStore())
    for _ in range(BURST.limit):
        await limiter.enforce("203.0.113.7", [BURST])

    await limiter.enforce("198.51.100.4", [BURST])


async def test_shared_limits_count_every_client() -> None:
    limiter = RateLimiter(InMemoryCounterStore())
    for client in ("198.51.100.1", "198.51.100.2", "198.51.100.3"):
        await limiter.enforce(client, [DAILY], [GLOBAL])

    with pytest.raises(RateLimitExceededError):
        await limiter.enforce("198.51.100.4", [DAILY], [GLOBAL])


async def test_rejected_clients_do_not_use_up_the_shared_limit() -> None:
    limiter = RateLimiter(InMemoryCounterStore())
    for _ in range(BURST.limit):
        await limiter.enforce("203.0.113.7", [BURST], [GLOBAL])
    for _ in range(GLOBAL.limit):
        with pytest.raises(RateLimitExceededError):
            await limiter.enforce("203.0.113.7", [BURST], [GLOBAL])

    await limiter.enforce("198.51.100.1", [BURST], [GLOBAL])


async def test_stores_hashed_client_keys() -> None:
    store = InMemoryCounterStore()

    await RateLimiter(store).enforce("203.0.113.7", [BURST])

    assert all("203.0.113.7" not in key for key in store.counts)


async def test_allows_requests_when_the_store_is_unavailable() -> None:
    limiter = RateLimiter(UnavailableCounterStore())

    for _ in range(BURST.limit + 3):
        await limiter.enforce("203.0.113.7", [BURST], [GLOBAL])
