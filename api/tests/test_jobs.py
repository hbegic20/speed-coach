from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.jobs import run_audit
from app.models.audit import AuditStatus
from app.services.audits import RUN_AUDIT_JOB, create_audit
from tests.fakes import RecordingQueue


def test_enqueued_job_name_matches_worker_function() -> None:
    assert run_audit.__name__ == RUN_AUDIT_JOB


async def test_run_audit_completes_the_audit(
    session_factory: async_sessionmaker[AsyncSession], job_queue: RecordingQueue
) -> None:
    async with session_factory() as session:
        audit = await create_audit(session, job_queue, "https://example.com/")

    await run_audit({"session_factory": session_factory}, str(audit.id))

    async with session_factory() as session:
        stored = await session.get(type(audit), audit.id)
        assert stored is not None
        assert stored.status is AuditStatus.COMPLETED
