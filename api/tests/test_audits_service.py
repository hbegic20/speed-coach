import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.audit import Audit, AuditFailureReason, AuditStatus, Platform
from app.models.device_report import Device
from app.schemas.report import DeviceReportData
from app.services.audits import (
    RUN_AUDIT_JOB,
    AuditQueueUnavailableError,
    create_audit,
    get_audit,
    process_audit,
)
from app.services.pagespeed import PageSpeedError
from tests.db import reload_audit
from tests.fakes import (
    RaisingCollector,
    RecordingQueue,
    StubCollector,
    StubDetector,
    UnavailableQueue,
    sample_report,
)


async def test_create_audit_stores_a_queued_audit_and_enqueues_it(
    session: AsyncSession, job_queue: RecordingQueue
) -> None:
    audit = await create_audit(session, job_queue, "https://example.com/")

    assert audit.url == "https://example.com/"
    assert audit.status is AuditStatus.QUEUED
    assert audit.failure_reason is None
    assert job_queue.jobs == [(RUN_AUDIT_JOB, (str(audit.id),))]


async def test_create_audit_marks_audit_failed_when_queue_is_unavailable(
    session: AsyncSession,
) -> None:
    with pytest.raises(AuditQueueUnavailableError):
        await create_audit(session, UnavailableQueue(), "https://example.com/")

    stored = (await session.scalars(select(Audit))).one()
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.QUEUE_UNAVAILABLE


async def test_get_audit_returns_none_for_unknown_id(session: AsyncSession) -> None:
    assert await get_audit(session, uuid.uuid4()) is None


SessionFactory = async_sessionmaker[AsyncSession]


async def queued_audit(session: AsyncSession) -> Audit:
    audit = Audit(url="https://example.com/", status=AuditStatus.QUEUED)
    session.add(audit)
    await session.commit()
    return audit


async def test_process_audit_stores_reports_and_completes(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)
    reports = [sample_report(Device.MOBILE, 41), sample_report(Device.DESKTOP, 88)]

    await process_audit(session, audit.id, StubCollector(reports), StubDetector())

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.COMPLETED
    assert stored.platform is Platform.WORDPRESS
    assert [DeviceReportData.model_validate(report) for report in stored.reports] == reports


async def test_process_audit_records_pagespeed_failures(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)
    collector = RaisingCollector(PageSpeedError(AuditFailureReason.SITE_UNREACHABLE))

    await process_audit(session, audit.id, collector, StubDetector())

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.SITE_UNREACHABLE
    assert stored.reports == []


async def test_process_audit_marks_unexpected_errors_and_reraises(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)

    with pytest.raises(RuntimeError):
        await process_audit(
            session, audit.id, RaisingCollector(RuntimeError("boom")), StubDetector()
        )

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.INTERNAL_ERROR


async def test_process_audit_ignores_unknown_audit(session: AsyncSession) -> None:
    await process_audit(session, uuid.uuid4(), StubCollector([]), StubDetector())

    assert (await session.scalars(select(Audit))).all() == []


async def test_process_audit_leaves_finished_audits_untouched(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = Audit(
        url="https://example.com/",
        status=AuditStatus.FAILED,
        failure_reason=AuditFailureReason.QUEUE_UNAVAILABLE,
    )
    session.add(audit)
    await session.commit()

    await process_audit(
        session, audit.id, StubCollector([sample_report(Device.MOBILE)]), StubDetector()
    )

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.reports == []


class ExplodingDetector:
    async def detect(self, url: str) -> Platform:
        raise RuntimeError("detector bug")


async def test_process_audit_marks_detector_bugs_as_internal_errors(
    session: AsyncSession, session_factory: SessionFactory
) -> None:
    audit = await queued_audit(session)
    collector = StubCollector([sample_report(Device.MOBILE)])

    with pytest.raises(RuntimeError):
        await process_audit(session, audit.id, collector, ExplodingDetector())

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.INTERNAL_ERROR
