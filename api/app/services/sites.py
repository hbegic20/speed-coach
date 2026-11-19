import uuid
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.owner import Owner
from app.models.audit import Audit, AuditStatus, Language
from app.models.completed_fix import CompletedFix
from app.models.device_report import Device
from app.models.tracked_site import TrackedSite
from app.schemas.site import CompletedFixResponse, LatestAudit, SiteCheck, SiteResponse
from app.services.audits import AuditQueue, AuditRequest, create_audit
from app.services.fix_progress import fix_progress

MAX_CHECKS_PER_SITE = 52


class SiteNotFoundError(Exception):
    pass


class SiteLimitReachedError(Exception):
    pass


async def track_site(
    session: AsyncSession,
    owner: Owner,
    url: str,
    audit_id: uuid.UUID | None,
    site_limit: int,
) -> TrackedSite:
    site = await _find_site_by_url(session, owner, url)
    if site is None:
        await _ensure_below_limit(session, owner, site_limit)
        site = await _create_site(session, owner, url)
    if audit_id is not None:
        await _attach_audit(session, site, audit_id)
    await session.commit()
    return site


async def list_sites(session: AsyncSession, owner: Owner) -> list[SiteResponse]:
    sites = (
        await session.scalars(
            select(TrackedSite)
            .where(TrackedSite.owner_key_hash == owner.key_hash)
            .order_by(TrackedSite.created_at)
        )
    ).all()
    audits_by_site = await _audits_by_site(session, [site.id for site in sites])
    return [site_response(site, audits_by_site[site.id]) for site in sites]


async def get_site(session: AsyncSession, owner: Owner, site_id: uuid.UUID) -> SiteResponse:
    site = await _owned_site(session, owner, site_id)
    audits_by_site = await _audits_by_site(session, [site.id])
    return site_response(site, audits_by_site[site.id])


async def recheck_site(
    session: AsyncSession,
    queue: AuditQueue,
    owner: Owner,
    site_id: uuid.UUID,
    language: Language,
) -> Audit:
    site = await _owned_site(session, owner, site_id)
    return await create_audit(
        session, queue, AuditRequest(url=site.url, language=language, tracked_site_id=site.id)
    )


async def set_completed_fixes(
    session: AsyncSession,
    owner: Owner,
    site_id: uuid.UUID,
    lighthouse_ids: list[str],
    *,
    completed: bool,
) -> None:
    site = await _owned_site(session, owner, site_id)
    existing = {fix.lighthouse_id: fix for fix in site.completed_fixes}
    requested = set(lighthouse_ids)
    if completed:
        site.completed_fixes.extend(
            CompletedFix(lighthouse_id=lighthouse_id)
            for lighthouse_id in requested - existing.keys()
        )
    else:
        for lighthouse_id in requested & existing.keys():
            site.completed_fixes.remove(existing[lighthouse_id])
    await session.commit()


async def untrack_site(session: AsyncSession, owner: Owner, site_id: uuid.UUID) -> None:
    site = await _owned_site(session, owner, site_id)
    await session.delete(site)
    await session.commit()


def site_response(site: TrackedSite, audits: list[Audit]) -> SiteResponse:
    completed = [audit for audit in audits if audit.status is AuditStatus.COMPLETED]
    latest = audits[-1] if audits else None
    return SiteResponse(
        id=site.id,
        url=site.url,
        created_at=site.created_at,
        latest_audit=LatestAudit(audit_id=latest.id, status=latest.status) if latest else None,
        checks=[_site_check(audit) for audit in completed[-MAX_CHECKS_PER_SITE:]],
        completed_fixes=[
            CompletedFixResponse(lighthouse_id=fix.lighthouse_id, completed_at=fix.completed_at)
            for fix in site.completed_fixes
        ],
        fix_progress=fix_progress(completed[-1] if completed else None, site.completed_fixes),
    )


def _site_check(audit: Audit) -> SiteCheck:
    scores = {report.device: report.performance_score for report in audit.reports}
    return SiteCheck(
        audit_id=audit.id,
        checked_at=audit.updated_at,
        platform=audit.platform,
        mobile_performance_score=scores.get(Device.MOBILE),
        desktop_performance_score=scores.get(Device.DESKTOP),
    )


async def _audits_by_site(
    session: AsyncSession, site_ids: list[uuid.UUID]
) -> defaultdict[uuid.UUID, list[Audit]]:
    grouped: defaultdict[uuid.UUID, list[Audit]] = defaultdict(list)
    if not site_ids:
        return grouped
    audits = await session.scalars(
        select(Audit).where(Audit.tracked_site_id.in_(site_ids)).order_by(Audit.created_at)
    )
    for audit in audits:
        if audit.tracked_site_id is not None:
            grouped[audit.tracked_site_id].append(audit)
    return grouped


async def _ensure_below_limit(session: AsyncSession, owner: Owner, site_limit: int) -> None:
    tracked = await session.scalar(
        select(func.count())
        .select_from(TrackedSite)
        .where(TrackedSite.owner_key_hash == owner.key_hash)
    )
    if (tracked or 0) >= site_limit:
        raise SiteLimitReachedError


async def _owned_site(session: AsyncSession, owner: Owner, site_id: uuid.UUID) -> TrackedSite:
    site = await session.get(TrackedSite, site_id)
    if site is None or site.owner_key_hash != owner.key_hash:
        raise SiteNotFoundError
    return site


async def _find_site_by_url(session: AsyncSession, owner: Owner, url: str) -> TrackedSite | None:
    return await session.scalar(
        select(TrackedSite).where(
            TrackedSite.owner_key_hash == owner.key_hash, TrackedSite.url == url
        )
    )


async def _create_site(session: AsyncSession, owner: Owner, url: str) -> TrackedSite:
    site = TrackedSite(owner_key_hash=owner.key_hash, url=url)
    session.add(site)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        existing = await _find_site_by_url(session, owner, url)
        if existing is None:
            raise
        return existing
    await session.refresh(site)
    return site


async def _attach_audit(session: AsyncSession, site: TrackedSite, audit_id: uuid.UUID) -> None:
    audit = await session.get(Audit, audit_id)
    if audit is not None and audit.url == site.url and audit.tracked_site_id is None:
        audit.tracked_site_id = site.id
