import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.audit import AuditStatus, Language, Platform
from app.schemas.public_url import PublicHttpUrl


class SiteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: PublicHttpUrl
    audit_id: uuid.UUID | None = None


class SiteRecheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Language


class SiteCheck(BaseModel):
    audit_id: uuid.UUID
    checked_at: datetime
    platform: Platform | None
    mobile_performance_score: int | None
    desktop_performance_score: int | None


class LatestAudit(BaseModel):
    audit_id: uuid.UUID
    status: AuditStatus


class SiteResponse(BaseModel):
    id: uuid.UUID
    url: str
    created_at: datetime
    latest_audit: LatestAudit | None
    checks: list[SiteCheck]
