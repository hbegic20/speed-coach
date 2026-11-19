import httpx
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.jobs import run_audit
from app.models.audit import Audit, AuditFailureReason, AuditStatus
from app.models.device_report import Device
from app.services.audits import RUN_AUDIT_JOB
from tests.db import reload_audit
from tests.fakes import InMemoryStore
from tests.pagespeed_payloads import lighthouse_payload

SessionFactory = async_sessionmaker[AsyncSession]


def worker_settings() -> Settings:
    return Settings.model_validate(
        {
            "database_url": "postgresql+asyncpg://user:password@localhost/speedcoach",
            "redis_url": "redis://localhost:6379/0",
            "pagespeed_api_key": SecretStr("test-api-key"),
        }
    )


def pagespeed_responding(status_code: int, scores: dict[str, float]) -> httpx.AsyncClient:
    def handler(request: httpx.Request) -> httpx.Response:
        strategy = request.url.params["strategy"]
        return httpx.Response(status_code, json=lighthouse_payload(score=scores[strategy]))

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def stored_audit(session_factory: SessionFactory, status: AuditStatus) -> Audit:
    async with session_factory() as session:
        audit = Audit(url="https://example.com/", status=status)
        session.add(audit)
        await session.commit()
        return audit


def test_enqueued_job_name_matches_worker_function() -> None:
    assert run_audit.__name__ == RUN_AUDIT_JOB


async def test_run_audit_stores_mobile_and_desktop_reports(
    session_factory: SessionFactory,
) -> None:
    audit = await stored_audit(session_factory, AuditStatus.QUEUED)
    context = {
        "session_factory": session_factory,
        "settings": worker_settings(),
        "http_client": pagespeed_responding(200, {"mobile": 0.37, "desktop": 0.81}),
        "redis": InMemoryStore(),
    }

    await run_audit(context, str(audit.id))

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.COMPLETED
    assert {report.device: report.performance_score for report in stored.reports} == {
        Device.MOBILE: 37,
        Device.DESKTOP: 81,
    }


async def test_run_audit_records_quota_exhaustion(session_factory: SessionFactory) -> None:
    audit = await stored_audit(session_factory, AuditStatus.QUEUED)
    context = {
        "session_factory": session_factory,
        "settings": worker_settings(),
        "http_client": pagespeed_responding(429, {"mobile": 0, "desktop": 0}),
        "redis": InMemoryStore(),
    }

    await run_audit(context, str(audit.id))

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.PAGESPEED_QUOTA_EXCEEDED
