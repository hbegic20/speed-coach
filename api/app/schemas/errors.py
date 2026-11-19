from enum import StrEnum

from pydantic import BaseModel


class ErrorCode(StrEnum):
    AUDIT_NOT_FOUND = "audit_not_found"
    AUDIT_QUEUE_UNAVAILABLE = "audit_queue_unavailable"
    OWNER_TOKEN_INVALID = "owner_token_invalid"
    SITE_NOT_FOUND = "site_not_found"


class ErrorResponse(BaseModel):
    detail: ErrorCode
