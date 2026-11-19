import secrets
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.owner import owner_from_token
from app.models.audit import Audit, AuditStatus, Language
from app.models.tracked_site import TrackedSite
from app.services.audits import RUN_AUDIT_JOB, AuditQueueUnavailableError
from app.services.scheduled_checks import SchedulePolicy, due_checks, schedule_checks
from app.services.sites import track_site
from tests.fakes import RecordingQueue, UnavailableQueue

SITE_LIMIT = 10

NOW = datetime(2026, 11, 23, 5, 0, tzinfo=UTC)
WEEKLY = SchedulePolicy(min_interval=timedelta(days=6), spacing_seconds=20)


async def tracked(session: AsyncSession, url: str) -> TrackedSite:
    return await track_site(
        session, owner_from_token(secrets.token_urlsafe(32)), url, None, SITE_LIMIT
    )


async def previous_check(
    session: AsyncSession,
    site: TrackedSite,
    *,
    days_ago: float,
    status: AuditStatus = AuditStatus.COMPLETED,
    language: Language = Language.ENGLISH,
) -> None:
    created = NOW - timedelta(days=days_ago)
    session.add(
        Audit(
            url=site.url,
            language=language,
            status=status,
            tracked_site_id=site.id,
            created_at=created,
            updated_at=created,
        )
    )
    await session.commit()


async def due_site_ids(session: AsyncSession) -> list[uuid.UUID]:
    return [check.site_id for check in await due_checks(session, NOW, WEEKLY.min_interval)]


async def test_never_checked_sites_are_due_in_bosnian(session: AsyncSession) -> None:
    site = await tracked(session, "https://new.example/")

    [check] = await due_checks(session, NOW, WEEKLY.min_interval)

    assert check.site_id == site.id
    assert check.language is Language.BOSNIAN


async def test_sites_checked_over_a_week_ago_are_due_in_their_last_language(
    session: AsyncSession,
) -> None:
    site = await tracked(session, "https://weekly.example/")
    await previous_check(session, site, days_ago=14, language=Language.BOSNIAN)
    await previous_check(session, site, days_ago=7, language=Language.ENGLISH)

    [check] = await due_checks(session, NOW, WEEKLY.min_interval)

    assert check.site_id == site.id
    assert check.language is Language.ENGLISH


@pytest.mark.parametrize(
    "status", [AuditStatus.COMPLETED, AuditStatus.FAILED, AuditStatus.RUNNING, AuditStatus.QUEUED]
)
async def test_recently_checked_sites_are_skipped(
    session: AsyncSession, status: AuditStatus
) -> None:
    site = await tracked(session, "https://fresh.example/")
    await previous_check(session, site, days_ago=2, status=status)

    assert await due_site_ids(session) == []


async def test_schedules_staggered_tracked_audits(
    session: AsyncSession, job_queue: RecordingQueue
) -> None:
    sites = [await tracked(session, f"https://site-{index}.example/") for index in range(3)]

    scheduled = await schedule_checks(session, job_queue, NOW, WEEKLY)

    assert scheduled == len(sites)
    audits = (await session.scalars(select(Audit).order_by(Audit.created_at))).all()
    assert [audit.tracked_site_id for audit in audits] == [site.id for site in sites]
    assert all(audit.status is AuditStatus.QUEUED for audit in audits)
    assert job_queue.jobs == [(RUN_AUDIT_JOB, (str(audit.id),)) for audit in audits]
    assert job_queue.delays == [0, 20, 40]


async def test_does_nothing_without_due_sites(
    session: AsyncSession, job_queue: RecordingQueue
) -> None:
    site = await tracked(session, "https://fresh.example/")
    await previous_check(session, site, days_ago=1)

    assert await schedule_checks(session, job_queue, NOW, WEEKLY) == 0
    assert job_queue.jobs == []


async def test_stops_when_the_queue_is_unavailable(session: AsyncSession) -> None:
    await tracked(session, "https://first.example/")
    await tracked(session, "https://second.example/")

    with pytest.raises(AuditQueueUnavailableError):
        await schedule_checks(session, UnavailableQueue(), NOW, WEEKLY)

    audits = (await session.scalars(select(Audit))).all()
    assert len(audits) == 1
