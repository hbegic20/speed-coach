from app.models.device_report import Device
from app.services.report_cache import ReportCache, cache_key
from tests.fakes import InMemoryStore, UnavailableStore, sample_report

URL = "https://example.com/"


async def test_returns_a_stored_report() -> None:
    cache = ReportCache(InMemoryStore(), ttl_seconds=900)
    report = sample_report(Device.MOBILE)

    await cache.put(URL, report)

    assert await cache.get(URL, Device.MOBILE) == report


async def test_misses_for_another_device_or_url() -> None:
    cache = ReportCache(InMemoryStore(), ttl_seconds=900)
    await cache.put(URL, sample_report(Device.MOBILE))

    assert await cache.get(URL, Device.DESKTOP) is None
    assert await cache.get("https://other.example.com/", Device.MOBILE) is None


async def test_stores_reports_with_the_configured_ttl() -> None:
    store = InMemoryStore()

    await ReportCache(store, ttl_seconds=120).put(URL, sample_report(Device.DESKTOP))

    assert store.expirations == {cache_key(URL, Device.DESKTOP): 120}


async def test_discards_malformed_entries() -> None:
    store = InMemoryStore()
    store.values[cache_key(URL, Device.MOBILE)] = '{"device": "mobile"}'

    assert await ReportCache(store, ttl_seconds=900).get(URL, Device.MOBILE) is None


async def test_keeps_working_when_store_is_unavailable() -> None:
    cache = ReportCache(UnavailableStore(), ttl_seconds=900)

    await cache.put(URL, sample_report(Device.MOBILE))

    assert await cache.get(URL, Device.MOBILE) is None
