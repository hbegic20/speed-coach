from typing import Any

from arq.jobs import Job
from redis.exceptions import ConnectionError as RedisConnectionError

from app.models.audit import AuditFailureReason, Language, Platform
from app.models.device_report import Device
from app.schemas.recommendation import RecommendationSet
from app.schemas.report import DeviceReportData, Finding
from app.services.audits import AuditServices
from app.services.pagespeed import PageSpeedError
from app.services.recommendations import RecommendationsUnavailableError
from tests.gemini_payloads import sample_recommendation_set


class RecordingQueue:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple[Any, ...]]] = []

    async def enqueue_job(self, function: str, *args: Any) -> Job | None:
        self.jobs.append((function, args))
        return None


class UnavailableQueue:
    async def enqueue_job(self, function: str, *args: Any) -> Job | None:
        raise RedisConnectionError("Redis is unreachable")


class InMemoryStore:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expirations: dict[str, int] = {}

    async def get(self, name: str) -> bytes | None:
        value = self.values.get(name)
        return value.encode() if value is not None else None

    async def set(self, name: str, value: str, ex: int) -> object:
        self.values[name] = value
        self.expirations[name] = ex
        return True


class UnavailableStore:
    async def get(self, name: str) -> bytes | None:
        raise RedisConnectionError("Redis is unreachable")

    async def set(self, name: str, value: str, ex: int) -> object:
        raise RedisConnectionError("Redis is unreachable")


def sample_report(device: Device, performance_score: int = 64) -> DeviceReportData:
    return DeviceReportData(
        device=device,
        performance_score=performance_score,
        accessibility_score=78,
        best_practices_score=83,
        seo_score=91,
        first_contentful_paint_ms=1500.0,
        largest_contentful_paint_ms=3100.0,
        total_blocking_time_ms=210.0,
        cumulative_layout_shift=0.05,
        speed_index_ms=2800.0,
        findings=[
            Finding(
                lighthouse_id="render-blocking-resources",
                title="Eliminate render-blocking resources",
                description="Resources are blocking the first paint of your page.",
                score=0,
                display_value="Est savings of 900 ms",
                savings_ms=900,
                savings_bytes=None,
            )
        ],
    )


class RecordingFetcher:
    def __init__(self) -> None:
        self.requests: list[tuple[str, Device]] = []

    async def fetch_report(self, url: str, device: Device) -> DeviceReportData:
        self.requests.append((url, device))
        return sample_report(device)


class FailingFetcher:
    def __init__(self, reason: AuditFailureReason) -> None:
        self.reason = reason

    async def fetch_report(self, url: str, device: Device) -> DeviceReportData:
        raise PageSpeedError(self.reason)


class StubCollector:
    def __init__(self, reports: list[DeviceReportData]) -> None:
        self.reports = reports

    async def collect(self, url: str) -> list[DeviceReportData]:
        return self.reports


class RaisingCollector:
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def collect(self, url: str) -> list[DeviceReportData]:
        raise self.error


class StubDetector:
    def __init__(self, platform: Platform = Platform.WORDPRESS) -> None:
        self.platform = platform

    async def detect(self, url: str) -> Platform:
        return self.platform


class RecordingWriter:
    def __init__(self, recommendation_set: RecommendationSet | None = None) -> None:
        self.recommendation_set = recommendation_set or sample_recommendation_set()
        self.calls: list[tuple[str, Platform, Language]] = []

    async def write(
        self,
        url: str,
        platform: Platform,
        language: Language,
        reports: list[DeviceReportData],
    ) -> RecommendationSet:
        self.calls.append((url, platform, language))
        return self.recommendation_set


class UnavailableWriter:
    async def write(
        self,
        url: str,
        platform: Platform,
        language: Language,
        reports: list[DeviceReportData],
    ) -> RecommendationSet:
        raise RecommendationsUnavailableError


def stub_services(
    reports: list[DeviceReportData] | None = None,
    platform: Platform = Platform.WORDPRESS,
    writer: RecordingWriter | UnavailableWriter | None = None,
) -> AuditServices:
    return AuditServices(
        collector=StubCollector(reports if reports is not None else []),
        detector=StubDetector(platform),
        writer=writer or RecordingWriter(),
    )


class InMemoryCounterStore:
    def __init__(self) -> None:
        self.counts: dict[str, int] = {}
        self.windows: dict[str, int] = {}

    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        self.counts[key] = self.counts.get(key, 0) + 1
        self.windows.setdefault(key, window_seconds)
        return self.counts[key], self.windows[key]


class UnavailableCounterStore:
    async def increment(self, key: str, window_seconds: int) -> tuple[int, int]:
        raise RedisConnectionError("Redis is unreachable")
