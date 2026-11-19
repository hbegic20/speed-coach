import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.dependencies import DbSession, JobQueue, SettingsDependency
from app.core.owner import CurrentOwner
from app.core.rate_limits import limit_audit_creation, limit_site_tracking
from app.schemas.audit import AuditResponse
from app.schemas.errors import ErrorCode, ErrorResponse
from app.schemas.site import (
    CompletedFixesUpdate,
    SiteCreate,
    SiteRecheck,
    SiteResponse,
    SitesResponse,
)
from app.services.audits import AuditQueueUnavailableError
from app.services.sites import (
    SiteLimitReachedError,
    SiteNotFoundError,
    get_site,
    list_sites,
    recheck_site,
    set_completed_fixes,
    track_site,
    untrack_site,
)

router = APIRouter(
    prefix="/sites",
    tags=["sites"],
    responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
)

NOT_FOUND_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}
}


RATE_LIMITED_RESPONSE: dict[int | str, dict[str, Any]] = {
    status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse}
}


def site_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.SITE_NOT_FOUND)


@router.get("")
async def read_sites(
    owner: CurrentOwner, session: DbSession, settings: SettingsDependency
) -> SitesResponse:
    return SitesResponse(
        sites=await list_sites(session, owner), site_limit=settings.max_sites_per_owner
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(limit_site_tracking)],
    responses={
        **RATE_LIMITED_RESPONSE,
        status.HTTP_409_CONFLICT: {"model": ErrorResponse},
    },
)
async def create_site(
    payload: SiteCreate, owner: CurrentOwner, session: DbSession, settings: SettingsDependency
) -> SiteResponse:
    try:
        site = await track_site(
            session, owner, str(payload.url), payload.audit_id, settings.max_sites_per_owner
        )
    except SiteLimitReachedError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=ErrorCode.SITE_LIMIT_REACHED
        ) from error
    return await get_site(session, owner, site.id)


@router.get("/{site_id}", responses=NOT_FOUND_RESPONSE)
async def read_site(site_id: uuid.UUID, owner: CurrentOwner, session: DbSession) -> SiteResponse:
    try:
        return await get_site(session, owner, site_id)
    except SiteNotFoundError as error:
        raise site_not_found() from error


@router.post(
    "/{site_id}/audits",
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(limit_audit_creation)],
    responses={
        **NOT_FOUND_RESPONSE,
        **RATE_LIMITED_RESPONSE,
        status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
    },
)
async def recheck(
    site_id: uuid.UUID,
    payload: SiteRecheck,
    owner: CurrentOwner,
    session: DbSession,
    queue: JobQueue,
) -> AuditResponse:
    try:
        audit = await recheck_site(session, queue, owner, site_id, payload.language)
    except SiteNotFoundError as error:
        raise site_not_found() from error
    except AuditQueueUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorCode.AUDIT_QUEUE_UNAVAILABLE,
        ) from error
    return AuditResponse.model_validate(audit)


@router.put(
    "/{site_id}/completed-fixes",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=NOT_FOUND_RESPONSE,
)
async def update_completed_fixes(
    site_id: uuid.UUID, payload: CompletedFixesUpdate, owner: CurrentOwner, session: DbSession
) -> Response:
    try:
        await set_completed_fixes(
            session, owner, site_id, payload.lighthouse_ids, completed=payload.completed
        )
    except SiteNotFoundError as error:
        raise site_not_found() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{site_id}", status_code=status.HTTP_204_NO_CONTENT, responses=NOT_FOUND_RESPONSE)
async def delete_site(site_id: uuid.UUID, owner: CurrentOwner, session: DbSession) -> Response:
    try:
        await untrack_site(session, owner, site_id)
    except SiteNotFoundError as error:
        raise site_not_found() from error
    return Response(status_code=status.HTTP_204_NO_CONTENT)
