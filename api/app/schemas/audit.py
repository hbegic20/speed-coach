import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.audit import AuditFailureReason, AuditStatus
from app.schemas.public_url import PublicHttpUrl
from app.schemas.report import DeviceReportData


class AuditCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: PublicHttpUrl


class AuditResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    url: str
    status: AuditStatus
    failure_reason: AuditFailureReason | None
    created_at: datetime
    updated_at: datetime
    reports: list[DeviceReportData]
