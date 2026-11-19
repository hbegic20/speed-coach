import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.owner import Owner, owner_from_token
from app.models.audit import Audit, AuditStatus, Language
from app.models.device_report import Device, DeviceReport
from app.models.tracked_site import OWNER_KEY_HASH_LENGTH
from app.services.sites import MAX_CHECKS_PER_SITE, get_site, list_sites, track_site
from tests.fakes import sample_report

URL = "https://example.com/"


def new_owner() -> Owner:
    return owner_from_token(secrets.token_urlsafe(32))


async def add_audit(
    session: AsyncSession,
    *,
    site_id: uuid.UUID | None,
    status: AuditStatus,
    mobile_score: int | None,
    minutes_ago: int,
) -> Audit:
    created = datetime.now(UTC) - timedelta(minutes=minutes_ago)
    audit = Audit(
        url=URL,
        language=Language.ENGLISH,
        status=status,
        tracked_site_id=site_id,
        created_at=created,
        updated_at=created,
    )
    session.add(audit)
    await session.flush()
    if mobile_score is not None:
        report = sample_report(Device.MOBILE, mobile_score)
        session.add(DeviceReport(audit_id=audit.id, **report.model_dump()))
    await session.commit()
    return audit


def test_owner_tokens_are_stored_only_as_hashes() -> None:
    token = secrets.token_urlsafe(32)

    owner = owner_from_token(token)

    assert token not in owner.key_hash
    assert len(owner.key_hash) == OWNER_KEY_HASH_LENGTH
    assert owner_from_token(token) == owner


async def test_history_lists_completed_checks_oldest_first(session: AsyncSession) -> None:
    owner = new_owner()
    site = await track_site(session, owner, URL, None)
    first = await add_audit(
        session, site_id=site.id, status=AuditStatus.COMPLETED, mobile_score=41, minutes_ago=30
    )
    await add_audit(
        session, site_id=site.id, status=AuditStatus.FAILED, mobile_score=None, minutes_ago=20
    )
    second = await add_audit(
        session, site_id=site.id, status=AuditStatus.COMPLETED, mobile_score=67, minutes_ago=10
    )
    running = await add_audit(
        session, site_id=site.id, status=AuditStatus.RUNNING, mobile_score=None, minutes_ago=1
    )

    response = await get_site(session, owner, site.id)

    assert [check.audit_id for check in response.checks] == [first.id, second.id]
    assert [check.mobile_performance_score for check in response.checks] == [41, 67]
    assert response.latest_audit is not None
    assert response.latest_audit.audit_id == running.id


async def test_history_keeps_only_the_most_recent_checks(session: AsyncSession) -> None:
    owner = new_owner()
    site = await track_site(session, owner, URL, None)
    for minutes_ago in range(MAX_CHECKS_PER_SITE + 3, 0, -1):
        await add_audit(
            session,
            site_id=site.id,
            status=AuditStatus.COMPLETED,
            mobile_score=50,
            minutes_ago=minutes_ago,
        )

    response = await get_site(session, owner, site.id)

    assert len(response.checks) == MAX_CHECKS_PER_SITE


async def test_tracking_does_not_take_over_audits_of_other_urls_or_sites(
    session: AsyncSession,
) -> None:
    owner = new_owner()
    other_page = Audit(
        url="https://other.example/", language=Language.ENGLISH, status=AuditStatus.COMPLETED
    )
    session.add(other_page)
    await session.commit()
    first_site = await track_site(session, new_owner(), URL, None)
    claimed = await add_audit(
        session, site_id=first_site.id, status=AuditStatus.COMPLETED, mobile_score=60, minutes_ago=4
    )

    site = await track_site(session, owner, URL, other_page.id)
    site = await track_site(session, owner, URL, claimed.id)

    assert (await get_site(session, owner, site.id)).checks == []


async def test_list_sites_returns_sites_in_the_order_they_were_tracked(
    session: AsyncSession,
) -> None:
    owner = new_owner()
    await track_site(session, owner, "https://first.example/", None)
    await track_site(session, owner, "https://second.example/", None)

    sites = await list_sites(session, owner)

    assert [site.url for site in sites] == ["https://first.example/", "https://second.example/"]
