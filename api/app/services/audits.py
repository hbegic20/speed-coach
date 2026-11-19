import logging
import uuid
from typing import Any, Protocol

from arq.jobs import Job
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit, AuditFailureReason, AuditStatus

logger = logging.getLogger(__name__)

RUN_AUDIT_JOB = "run_audit"
TERMINAL_STATUSES = frozenset({AuditStatus.COMPLETED, AuditStatus.FAILED})


class AuditQueue(Protocol):
    async def enqueue_job(self, function: str, *args: Any) -> Job | None: ...


class AuditQueueUnavailableError(Exception):
    pass


async def create_audit(session: AsyncSession, queue: AuditQueue, url: str) -> Audit:
    audit = Audit(url=url, status=AuditStatus.QUEUED)
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


async def process_audit(session: AsyncSession, audit_id: uuid.UUID) -> None:
    audit = await session.get(Audit, audit_id)
    if audit is None:
        logger.warning("Audit %s no longer exists, skipping", audit_id)
        return
    if audit.status in TERMINAL_STATUSES:
        logger.info("Audit %s already %s, skipping", audit_id, audit.status)
        return

    await _set_status(session, audit, AuditStatus.RUNNING)
    await _set_status(session, audit, AuditStatus.COMPLETED)


async def _set_status(session: AsyncSession, audit: Audit, status: AuditStatus) -> None:
    audit.status = status
    await session.commit()


async def _fail(session: AsyncSession, audit: Audit, reason: AuditFailureReason) -> None:
    audit.failure_reason = reason
    await _set_status(session, audit, AuditStatus.FAILED)
