import asyncio
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Protocol

from arq.jobs import Job
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit, AuditFailureReason, AuditStatus, Language, Platform
from app.models.device_report import DeviceReport
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationSet
from app.schemas.report import DeviceReportData
from app.services.pagespeed import PageSpeedError
from app.services.recommendations import RecommendationsUnavailableError, has_findings

logger = logging.getLogger(__name__)

RUN_AUDIT_JOB = "run_audit"
TERMINAL_STATUSES = frozenset({AuditStatus.COMPLETED, AuditStatus.FAILED})


class AuditQueue(Protocol):
    async def enqueue_job(self, function: str, *args: Any) -> Job | None: ...


class ReportCollector(Protocol):
    async def collect(self, url: str) -> list[DeviceReportData]: ...


class PlatformDetector(Protocol):
    async def detect(self, url: str) -> Platform: ...


class RecommendationWriter(Protocol):
    async def write(
        self,
        url: str,
        platform: Platform,
        language: Language,
        reports: list[DeviceReportData],
    ) -> RecommendationSet: ...


@dataclass(frozen=True)
class AuditServices:
    collector: ReportCollector
    detector: PlatformDetector
    writer: RecommendationWriter


class AuditQueueUnavailableError(Exception):
    pass


class _AuditFailedError(Exception):
    def __init__(self, reason: AuditFailureReason) -> None:
        super().__init__(reason.value)
        self.reason = reason


async def create_audit(
    session: AsyncSession,
    queue: AuditQueue,
    url: str,
    language: Language,
    tracked_site_id: uuid.UUID | None = None,
) -> Audit:
    audit = Audit(
        url=url, language=language, status=AuditStatus.QUEUED, tracked_site_id=tracked_site_id
    )
    session.add(audit)
    await session.commit()

    try:
        await queue.enqueue_job(RUN_AUDIT_JOB, str(audit.id))
    except (RedisError, OSError) as error:
        logger.exception("Failed to enqueue audit %s", audit.id)
        await _fail(session, audit, AuditFailureReason.QUEUE_UNAVAILABLE)
        raise AuditQueueUnavailableError from error

    await session.refresh(audit)
    return audit


async def get_audit(session: AsyncSession, audit_id: uuid.UUID) -> Audit | None:
    return await session.get(Audit, audit_id)


async def process_audit(
    session: AsyncSession, audit_id: uuid.UUID, services: AuditServices
) -> None:
    audit = await session.get(Audit, audit_id)
    if audit is None:
        logger.warning("Audit %s no longer exists, skipping", audit_id)
        return
    if audit.status in TERMINAL_STATUSES:
        logger.info("Audit %s already %s, skipping", audit_id, audit.status)
        return

    await _set_status(session, audit, AuditStatus.RUNNING)
    try:
        await _run_pipeline(session, audit, services)
    except _AuditFailedError as error:
        await _fail(session, audit, error.reason)
        return
    except Exception:
        await _fail(session, audit, AuditFailureReason.INTERNAL_ERROR)
        raise
    await _set_status(session, audit, AuditStatus.COMPLETED)


async def _run_pipeline(session: AsyncSession, audit: Audit, services: AuditServices) -> None:
    reports, platform = await _inspect_site(audit.url, services)
    audit.platform = platform
    session.add_all(DeviceReport(audit_id=audit.id, **report.model_dump()) for report in reports)
    await session.commit()

    if not has_findings(reports):
        return
    recommendation_set = await _write_recommendations(audit, platform, reports, services)
    audit.summary = recommendation_set.summary
    session.add_all(_recommendation_rows(audit.id, recommendation_set))


async def _inspect_site(
    url: str, services: AuditServices
) -> tuple[list[DeviceReportData], Platform]:
    try:
        async with asyncio.TaskGroup() as task_group:
            reports = task_group.create_task(services.collector.collect(url))
            platform = task_group.create_task(services.detector.detect(url))
    except ExceptionGroup as errors:
        first_error = errors.exceptions[0]
        if isinstance(first_error, PageSpeedError):
            raise _AuditFailedError(first_error.reason) from first_error
        raise first_error from None
    return reports.result(), platform.result()


async def _write_recommendations(
    audit: Audit, platform: Platform, reports: list[DeviceReportData], services: AuditServices
) -> RecommendationSet:
    try:
        return await services.writer.write(audit.url, platform, audit.language, reports)
    except RecommendationsUnavailableError as error:
        raise _AuditFailedError(AuditFailureReason.RECOMMENDATIONS_UNAVAILABLE) from error


def _recommendation_rows(
    audit_id: uuid.UUID, recommendation_set: RecommendationSet
) -> list[Recommendation]:
    return [
        Recommendation(
            audit_id=audit_id,
            rank=rank,
            title=draft.title,
            explanation=draft.explanation,
            steps=draft.steps,
            impact=draft.impact,
            effort=draft.effort,
            devices=[device.value for device in draft.devices],
            lighthouse_ids=draft.lighthouse_ids,
        )
        for rank, draft in enumerate(recommendation_set.recommendations, start=1)
    ]


async def _set_status(session: AsyncSession, audit: Audit, status: AuditStatus) -> None:
    audit.status = status
    await session.commit()


async def _fail(session: AsyncSession, audit: Audit, reason: AuditFailureReason) -> None:
    audit.failure_reason = reason
    await _set_status(session, audit, AuditStatus.FAILED)
