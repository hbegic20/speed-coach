import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

MAX_LIGHTHOUSE_ID_LENGTH = 128


class CompletedFix(Base):
    __tablename__ = "completed_fixes"
    __table_args__ = (UniqueConstraint("tracked_site_id", "lighthouse_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tracked_site_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracked_sites.id", ondelete="CASCADE")
    )
    lighthouse_id: Mapped[str] = mapped_column(String(MAX_LIGHTHOUSE_ID_LENGTH))
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), server_default=func.now()
    )
