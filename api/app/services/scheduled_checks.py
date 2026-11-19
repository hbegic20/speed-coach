import logging
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import Audit, Language
from app.models.tracked_site import TrackedSite
from app.services.audits import AuditQueue, AuditRequest, create_audit

logger = logging.getLogger(__name__)

DEFAULT_LANGUAGE = Language.BOSNIAN


@dataclass(frozen=True)
class DueCheck:
    site_id: uuid.UUID
    url: str
    language: Language


@dataclass(frozen=True)
class SchedulePolicy:
    min_interval: timedelta
    spacing_seconds: float


async def _latest_audit_per_site(session: AsyncSession) -> dict[uuid.UUID, Audit]:
    newest = (
        select(Audit.tracked_site_id, func.max(Audit.created_at).label("created_at"))
        .where(Audit.tracked_site_id.is_not(None))
        .group_by(Audit.tracked_site_id)
        .subquery()
    )
    audits = await session.scalars(
        select(Audit).join(
            newest,
            (Audit.tracked_site_id == newest.c.tracked_site_id)
            & (Audit.created_at == newest.c.created_at),
        )
    )
    return {audit.tracked_site_id: audit for audit in audits if audit.tracked_site_id}


async def due_checks(
    session: AsyncSession, now: datetime, min_interval: timedelta
) -> list[DueCheck]:
    recently_checked = select(Audit.tracked_site_id).where(
        Audit.tracked_site_id.is_not(None), Audit.created_at > now - min_interval
    )
    sites = (
        await session.scalars(
            select(TrackedSite)
            .where(TrackedSite.id.not_in(recently_checked))
            .order_by(TrackedSite.created_at)
        )
    ).all()
    latest = await _latest_audit_per_site(session)
    return [
        DueCheck(
            site_id=site.id,
            url=site.url,
            language=latest[site.id].language if site.id in latest else DEFAULT_LANGUAGE,
        )
        for site in sites
    ]


async def schedule_checks(
    session: AsyncSession, queue: AuditQueue, now: datetime, policy: SchedulePolicy
) -> int:
    checks = await due_checks(session, now, policy.min_interval)
    for position, check in enumerate(checks):
        await create_audit(
            session,
            queue,
            AuditRequest(url=check.url, language=check.language, tracked_site_id=check.site_id),
            defer_seconds=position * policy.spacing_seconds,
        )
    logger.info("Scheduled %s weekly checks", len(checks))
    return len(checks)
