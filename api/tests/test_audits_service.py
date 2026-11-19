import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit import Audit, AuditFailureReason, AuditStatus, Language, Platform
from app.models.device_report import Device
from app.schemas.recommendation import RecommendationResponse
from app.schemas.report import DeviceReportData
from app.services.audits import (
    RUN_AUDIT_JOB,
    AuditQueueUnavailableError,
    AuditServices,
    create_audit,
    get_audit,
    process_audit,
)
from app.services.pagespeed import PageSpeedError
from tests.db import reload_audit
from tests.fakes import (
    RaisingCollector,
    RecordingQueue,
    RecordingWriter,
    StubCollector,
    StubDetector,
    UnavailableQueue,
    UnavailableWriter,
    sample_report,
    stub_services,
)
from tests.gemini_payloads import sample_recommendation_set

SessionFactory = async_sessionmaker[AsyncSession]
URL = "https://example.com/"


def two_reports() -> list[DeviceReportData]:
    return [sample_report(Device.MOBILE, 41), sample_report(Device.DESKTOP, 88)]


async def queued_audit(session: AsyncSession, language: Language = Language.ENGLISH) -> Audit:
    audit = Audit(url=URL, language=language, status=AuditStatus.QUEUED)
    session.add(audit)
    await session.commit()
    return audit


async def test_create_audit_stores_a_queued_audit_and_enqueues_it(
    session: AsyncSession, job_queue: RecordingQueue
) -> None:
    audit = await create_audit(session, job_queue, URL, Language.BOSNIAN)

    assert audit.url == URL
    assert audit.language is Language.BOSNIAN
    assert audit.status is AuditStatus.QUEUED
    assert audit.failure_reason is None
    assert job_queue.jobs == [(RUN_AUDIT_JOB, (str(audit.id),))]


async def test_create_audit_marks_audit_failed_when_queue_is_unavailable(
    session: AsyncSession,
) -> None:
    with pytest.raises(AuditQueueUnavailableError):
        await create_audit(session, UnavailableQueue(), URL, Language.ENGLISH)

    stored = (await session.scalars(select(Audit))).one()
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.QUEUE_UNAVAILABLE


async def test_get_audit_returns_none_for_unknown_id(session: AsyncSession) -> None:
    assert await get_audit(session, uuid.uuid4()) is None


async def test_process_audit_stores_reports_platform_and_ranked_recommendations(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)
    reports = two_reports()

    await process_audit(session, audit.id, stub_services(reports))

    stored = await reload_audit(session_factory, audit.id)
    expected = sample_recommendation_set()
    assert stored.status is AuditStatus.COMPLETED
    assert stored.platform is Platform.WORDPRESS
    assert stored.summary == expected.summary
    assert [DeviceReportData.model_validate(report) for report in stored.reports] == reports
    assert [RecommendationResponse.model_validate(row) for row in stored.recommendations] == [
        RecommendationResponse(rank=rank, **draft.model_dump())
        for rank, draft in enumerate(expected.recommendations, start=1)
    ]


async def test_process_audit_writes_recommendations_in_the_audit_language(
    session: AsyncSession,
) -> None:
    audit = await queued_audit(session, Language.BOSNIAN)
    writer = RecordingWriter()

    await process_audit(session, audit.id, stub_services(two_reports(), Platform.SHOPIFY, writer))

    assert writer.calls == [(URL, Platform.SHOPIFY, Language.BOSNIAN)]


async def test_process_audit_skips_recommendations_when_nothing_needs_fixing(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)
    flawless = [report.model_copy(update={"findings": []}) for report in two_reports()]
    writer = RecordingWriter()

    await process_audit(session, audit.id, stub_services(flawless, writer=writer))

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.COMPLETED
    assert stored.summary is None
    assert stored.recommendations == []
    assert writer.calls == []


async def test_process_audit_keeps_reports_when_recommendations_fail(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)

    await process_audit(session, audit.id, stub_services(two_reports(), writer=UnavailableWriter()))

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.RECOMMENDATIONS_UNAVAILABLE
    assert stored.platform is Platform.WORDPRESS
    assert len(stored.reports) == len(two_reports())
    assert stored.recommendations == []


async def test_process_audit_records_pagespeed_failures(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)
    services = AuditServices(
        collector=RaisingCollector(PageSpeedError(AuditFailureReason.SITE_UNREACHABLE)),
        detector=StubDetector(),
        writer=RecordingWriter(),
    )

    await process_audit(session, audit.id, services)

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.SITE_UNREACHABLE
    assert stored.reports == []


async def test_process_audit_marks_unexpected_errors_and_reraises(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)
    services = AuditServices(
        collector=RaisingCollector(RuntimeError("boom")),
        detector=StubDetector(),
        writer=RecordingWriter(),
    )

    with pytest.raises(RuntimeError):
        await process_audit(session, audit.id, services)

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.INTERNAL_ERROR


class ExplodingDetector:
    async def detect(self, url: str) -> Platform:
        raise RuntimeError("detector bug")


async def test_process_audit_marks_detector_bugs_as_internal_errors(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)
    services = AuditServices(
        collector=StubCollector(two_reports()),
        detector=ExplodingDetector(),
        writer=RecordingWriter(),
    )

    with pytest.raises(RuntimeError):
        await process_audit(session, audit.id, services)

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.INTERNAL_ERROR


async def test_process_audit_ignores_unknown_audit(session: AsyncSession) -> None:
    await process_audit(session, uuid.uuid4(), stub_services())

    assert (await session.scalars(select(Audit))).all() == []


async def test_process_audit_leaves_finished_audits_untouched(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = Audit(
        url=URL,
        language=Language.ENGLISH,
        status=AuditStatus.FAILED,
        failure_reason=AuditFailureReason.QUEUE_UNAVAILABLE,
    )
    session.add(audit)
    await session.commit()

    await process_audit(session, audit.id, stub_services(two_reports()))

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.reports == []


async def test_recommendation_lighthouse_ids_survive_storage(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)
    writer = RecordingWriter(sample_recommendation_set(["render-blocking-resources", "unused-css"]))

    await process_audit(session, audit.id, stub_services(two_reports(), writer=writer))

    stored = await reload_audit(session_factory, audit.id)
    assert stored.recommendations[0].lighthouse_ids == ["render-blocking-resources", "unused-css"]
