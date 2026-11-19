import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.audit import AuditFailureReason, AuditStatus, Language, Platform
from app.schemas.public_url import PublicHttpUrl
from app.schemas.recommendation import RecommendationResponse
from app.schemas.report import DeviceReportData


class AuditCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: PublicHttpUrl
    language: Language


class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    language: Language
    tracked_site_id: uuid.UUID | None
    status: AuditStatus
    failure_reason: AuditFailureReason | None
    platform: Platform | None
    summary: str | None
    created_at: datetime
    updated_at: datetime
    reports: list[DeviceReportData]
    recommendations: list[RecommendationResponse]
