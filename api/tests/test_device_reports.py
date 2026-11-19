import pytest

from app.models.audit import AuditFailureReason
from app.models.device_report import Device
from app.services.device_reports import DeviceReportCollector
from app.services.pagespeed import PageSpeedError
from app.services.report_cache import ReportCache
from tests.fakes import FailingFetcher, InMemoryStore, RecordingFetcher, sample_report

URL = "https://example.com/"


async def test_collects_a_report_for_every_device() -> None:
    fetcher = RecordingFetcher()
    collector = DeviceReportCollector(fetcher, ReportCache(InMemoryStore(), ttl_seconds=900))

    reports = await collector.collect(URL)

    assert [report.device for report in reports] == [Device.MOBILE, Device.DESKTOP]
    assert sorted(fetcher.requests) == sorted([(URL, Device.MOBILE), (URL, Device.DESKTOP)])


async def test_reuses_cached_reports_instead_of_calling_pagespeed() -> None:
    cache = ReportCache(InMemoryStore(), ttl_seconds=900)
    await cache.put(URL, sample_report(Device.MOBILE, performance_score=91))
    fetcher = RecordingFetcher()

    reports = await DeviceReportCollector(fetcher, cache).collect(URL)

    assert reports[0].performance_score == sample_report(Device.MOBILE, 91).performance_score
    assert fetcher.requests == [(URL, Device.DESKTOP)]


async def test_caches_fresh_reports_for_the_next_audit() -> None:
    cache = ReportCache(InMemoryStore(), ttl_seconds=900)
    await DeviceReportCollector(RecordingFetcher(), cache).collect(URL)
    fetcher = RecordingFetcher()

    await DeviceReportCollector(fetcher, cache).collect(URL)

    assert fetcher.requests == []


async def test_raises_the_pagespeed_failure() -> None:
    fetcher = FailingFetcher(AuditFailureReason.PAGESPEED_QUOTA_EXCEEDED)
    collector = DeviceReportCollector(fetcher, ReportCache(InMemoryStore(), ttl_seconds=900))

    with pytest.raises(PageSpeedError) as raised:
        await collector.collect(URL)

    assert raised.value.reason is AuditFailureReason.PAGESPEED_QUOTA_EXCEEDED
