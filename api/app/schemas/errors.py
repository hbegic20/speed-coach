from enum import StrEnum

from pydantic import BaseModel


class ErrorCode(StrEnum):
    AUDIT_NOT_FOUND = "audit_not_found"
    AUDIT_QUEUE_UNAVAILABLE = "audit_queue_unavailable"


class ErrorResponse(BaseModel):
    detail: ErrorCode
