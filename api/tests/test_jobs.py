import ipaddress
import json
import secrets
from typing import Any

import httpx
from pydantic import SecretStr
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings
from app.core.owner import owner_from_token
from app.jobs import run_audit, run_scheduled_checks
from app.models.audit import Audit, AuditFailureReason, AuditStatus, Language, Platform
from app.models.device_report import Device
from app.services.audits import RUN_AUDIT_JOB
from app.services.gemini import INTERACTIONS_ENDPOINT
from app.services.page_fetch import IPAddress, PageFetcher
from app.services.pagespeed import PAGESPEED_ENDPOINT
from app.services.sites import track_site
from tests.db import reload_audit
from tests.fakes import InMemoryStore, RecordingQueue
from tests.gemini_payloads import recommendation_interaction, sample_recommendation_set
from tests.pagespeed_payloads import lighthouse_payload

SessionFactory = async_sessionmaker[AsyncSession]


def worker_settings() -> Settings:
    return Settings.model_validate(
        {
            "database_url": "postgresql+asyncpg://user:password@localhost/speedcoach",
            "redis_url": "redis://localhost:6379/0",
            "pagespeed_api_key": SecretStr("test-pagespeed-key"),
            "gemini_api_key": SecretStr("test-gemini-key"),
        }
    )


class GoogleApis:
    def __init__(self, pagespeed_status: int = 200) -> None:
        self.pagespeed_status = pagespeed_status
        self.gemini_requests: list[dict[str, Any]] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        if str(request.url).startswith(INTERACTIONS_ENDPOINT):
            self.gemini_requests.append(json.loads(request.content))
            return httpx.Response(200, json=recommendation_interaction(sample_recommendation_set()))
        if str(request.url).startswith(PAGESPEED_ENDPOINT):
            score = {"mobile": 0.37, "desktop": 0.81}[request.url.params["strategy"]]
            return httpx.Response(self.pagespeed_status, json=lighthouse_payload(score=score))
        return httpx.Response(404)

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(transport=httpx.MockTransport(self.handle))


async def resolve_to_public_address(host: str, port: int) -> list[IPAddress]:
    return [ipaddress.ip_address("93.184.215.14")]


def shopify_page_fetcher() -> PageFetcher:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, html='<script src="//cdn.shopify.com/s/theme.js"></script>')

    return PageFetcher(
        timeout_seconds=5,
        resolver=resolve_to_public_address,
        transport=httpx.MockTransport(handler),
    )


def worker_context(session_factory: SessionFactory, google: GoogleApis) -> dict[str, Any]:
    return {
        "session_factory": session_factory,
        "settings": worker_settings(),
        "http_client": google.client(),
        "redis": InMemoryStore(),
        "page_fetcher": shopify_page_fetcher(),
    }


async def stored_audit(session_factory: SessionFactory) -> Audit:
    async with session_factory() as session:
        audit = Audit(
            url="https://example.com/", language=Language.BOSNIAN, status=AuditStatus.QUEUED
        )
        session.add(audit)
        await session.commit()
        return audit


def test_enqueued_job_name_matches_worker_function() -> None:
    assert run_audit.__name__ == RUN_AUDIT_JOB


async def test_run_audit_produces_a_full_report(session_factory: SessionFactory) -> None:
    audit = await stored_audit(session_factory)
    google = GoogleApis()

    await run_audit(worker_context(session_factory, google), str(audit.id))

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.COMPLETED
    assert stored.platform is Platform.SHOPIFY
    assert {report.device: report.performance_score for report in stored.reports} == {
        Device.MOBILE: 37,
        Device.DESKTOP: 81,
    }
    assert stored.summary == sample_recommendation_set().summary
    assert [row.title for row in stored.recommendations] == [
        draft.title for draft in sample_recommendation_set().recommendations
    ]


async def test_run_audit_asks_gemini_in_the_audit_language_for_its_platform(
    session_factory: SessionFactory,
) -> None:
    audit = await stored_audit(session_factory)
    google = GoogleApis()

    await run_audit(worker_context(session_factory, google), str(audit.id))

    [request] = google.gemini_requests
    assert "Bosnian" in request["system_instruction"]
    assert '"platform": "shopify"' in request["input"]


async def test_run_audit_records_quota_exhaustion(session_factory: SessionFactory) -> None:
    audit = await stored_audit(session_factory)
    google = GoogleApis(pagespeed_status=429)

    await run_audit(worker_context(session_factory, google), str(audit.id))

    stored = await reload_audit(session_factory, audit.id)
    assert stored.status is AuditStatus.FAILED
    assert stored.failure_reason is AuditFailureReason.PAGESPEED_QUOTA_EXCEEDED
    assert google.gemini_requests == []


async def test_scheduled_checks_queue_every_due_site(
    session_factory: SessionFactory, session: AsyncSession, job_queue: RecordingQueue
) -> None:
    await track_site(
        session, owner_from_token(secrets.token_urlsafe(32)), "https://a.example/", None
    )

    scheduled = await run_scheduled_checks(
        {"settings": worker_settings(), "session_factory": session_factory, "redis": job_queue}
    )

    assert scheduled == 1
    assert len(job_queue.jobs) == 1


async def test_scheduled_checks_can_be_switched_off(
    session_factory: SessionFactory, session: AsyncSession, job_queue: RecordingQueue
) -> None:
    await track_site(
        session, owner_from_token(secrets.token_urlsafe(32)), "https://a.example/", None
    )
    disabled = worker_settings().model_copy(update={"scheduled_checks_enabled": False})

    scheduled = await run_scheduled_checks(
        {"settings": disabled, "session_factory": session_factory, "redis": job_queue}
    )

    assert scheduled == 0
    assert job_queue.jobs == []
