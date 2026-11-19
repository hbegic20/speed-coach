import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

MAX_URL_LENGTH = 2048


class AuditStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AuditFailureReason(StrEnum):
    QUEUE_UNAVAILABLE = "queue_unavailable"


def _string_enum(enum_class: type[StrEnum], length: int) -> Enum:
    return Enum(
        enum_class,
        native_enum=False,
        create_constraint=True,
        length=length,
        values_callable=lambda members: [member.value for member in members],
    )


class Audit(Base):
    __tablename__ = "audits"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    url: Mapped[str] = mapped_column(String(MAX_URL_LENGTH))
    status: Mapped[AuditStatus] = mapped_column(
        _string_enum(AuditStatus, 16), default=AuditStatus.QUEUED
    )
    failure_reason: Mapped[AuditFailureReason | None] = mapped_column(
        _string_enum(AuditFailureReason, 32)
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
