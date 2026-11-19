import uuid

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import DbSession, JobQueue
from app.schemas.audit import AuditCreate, AuditResponse
from app.schemas.errors import ErrorCode, ErrorResponse
from app.services.audits import AuditQueueUnavailableError, create_audit, get_audit

router = APIRouter(prefix="/audits", tags=["audits"])


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse}},
)
async def submit_audit(payload: AuditCreate, session: DbSession, queue: JobQueue) -> AuditResponse:
    try:
        audit = await create_audit(session, queue, str(payload.url), payload.language)
    except AuditQueueUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=ErrorCode.AUDIT_QUEUE_UNAVAILABLE,
        ) from error
    return AuditResponse.model_validate(audit)


@router.get(
    "/{audit_id}",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
async def read_audit(audit_id: uuid.UUID, session: DbSession) -> AuditResponse:
    audit = await get_audit(session, audit_id)
    if audit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=ErrorCode.AUDIT_NOT_FOUND)
    return AuditResponse.model_validate(audit)
