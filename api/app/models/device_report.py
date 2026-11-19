import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, string_enum


class Device(StrEnum):
    MOBILE = "mobile"
    DESKTOP = "desktop"


SCORE_COLUMNS = ("performance_score", "accessibility_score", "best_practices_score", "seo_score")


class DeviceReport(Base):
    __tablename__ = "device_reports"
    __table_args__ = (
        UniqueConstraint("audit_id", "device"),
        *(
            CheckConstraint(f"{column} BETWEEN 0 AND 100", name=f"device_reports_{column}_range")
            for column in SCORE_COLUMNS
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    audit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"))
    device: Mapped[Device] = mapped_column(string_enum(Device, 16))
    performance_score: Mapped[int] = mapped_column(SmallInteger)
    accessibility_score: Mapped[int | None] = mapped_column(SmallInteger)
    best_practices_score: Mapped[int | None] = mapped_column(SmallInteger)
    seo_score: Mapped[int | None] = mapped_column(SmallInteger)
    first_contentful_paint_ms: Mapped[float | None]
    largest_contentful_paint_ms: Mapped[float | None]
    total_blocking_time_ms: Mapped[float | None]
    cumulative_layout_shift: Mapped[float | None]
    speed_index_ms: Mapped[float | None]
    findings: Mapped[list[dict[str, Any]]] = mapped_column(JSON().with_variant(JSONB, "postgresql"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
