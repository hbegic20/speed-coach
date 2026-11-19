import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit, AuditFailureReason, AuditStatus
from app.services.audits import (
    RUN_AUDIT_JOB,
    AuditQueueUnavailableError,
    create_audit,
    get_audit,
    process_audit,
)
from tests.fakes import RecordingQueue, UnavailableQueue


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


async def test_process_audit_completes_a_queued_audit(
    session: AsyncSession, job_queue: RecordingQueue
) -> None:
    audit = await create_audit(session, job_queue, "https://example.com/")

    await process_audit(session, audit.id)

    assert audit.status is AuditStatus.COMPLETED


async def test_process_audit_ignores_unknown_audit(session: AsyncSession) -> None:
    await process_audit(session, uuid.uuid4())

    assert (await session.scalars(select(Audit))).all() == []


async def test_process_audit_leaves_finished_audits_untouched(session: AsyncSession) -> None:
    audit = Audit(
        url="https://example.com/",
        status=AuditStatus.FAILED,
        failure_reason=AuditFailureReason.QUEUE_UNAVAILABLE,
    )
    session.add(audit)
    await session.commit()

    await process_audit(session, audit.id)

    assert audit.status is AuditStatus.FAILED
