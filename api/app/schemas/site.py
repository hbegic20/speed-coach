import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.models.audit import AuditStatus, Language, Platform
from app.schemas.public_url import PublicHttpUrl


class SiteCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: PublicHttpUrl
    audit_id: uuid.UUID | None = None


class SiteRecheck(BaseModel):
    model_config = ConfigDict(extra="forbid")

    language: Language


LighthouseId = Annotated[str, StringConstraints(pattern=r"^[a-z0-9-]{1,128}$")]

MAX_FIXES_PER_UPDATE = 20


class CompletedFixesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lighthouse_ids: list[LighthouseId] = Field(min_length=1, max_length=MAX_FIXES_PER_UPDATE)
    completed: bool


class CompletedFixResponse(BaseModel):
    lighthouse_id: str
    completed_at: datetime


class FixProgress(BaseModel):
    completed: int
    total: int
    confirmed: int


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
    completed_fixes: list[CompletedFixResponse]
    fix_progress: FixProgress


class SitesResponse(BaseModel):
    sites: list[SiteResponse]
    site_limit: int
