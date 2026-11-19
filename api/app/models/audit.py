import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, string_enum
from app.models.device_report import DeviceReport

MAX_URL_LENGTH = 2048


class AuditStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditFailureReason(StrEnum):
    QUEUE_UNAVAILABLE = "queue_unavailable"
    SITE_UNREACHABLE = "site_unreachable"
    PAGESPEED_QUOTA_EXCEEDED = "pagespeed_quota_exceeded"
    PAGESPEED_UNAVAILABLE = "pagespeed_unavailable"
    INTERNAL_ERROR = "internal_error"


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(MAX_URL_LENGTH))
    status: Mapped[AuditStatus] = mapped_column(
        string_enum(AuditStatus, 16), default=AuditStatus.QUEUED
    )
    failure_reason: Mapped[AuditFailureReason | None] = mapped_column(
        string_enum(AuditFailureReason, 32)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    reports: Mapped[list[DeviceReport]] = relationship(
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by=DeviceReport.device.desc(),
    )
