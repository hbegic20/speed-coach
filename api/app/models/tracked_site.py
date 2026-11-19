import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.completed_fix import CompletedFix

OWNER_KEY_HASH_LENGTH = 64
MAX_SITE_URL_LENGTH = 2048


class TrackedSite(Base):
    __tablename__ = "tracked_sites"
    __table_args__ = (UniqueConstraint("owner_key_hash", "url"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_key_hash: Mapped[str] = mapped_column(String(OWNER_KEY_HASH_LENGTH))
    url: Mapped[str] = mapped_column(String(MAX_SITE_URL_LENGTH))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_fixes: Mapped[list[CompletedFix]] = relationship(
        lazy="selectin", cascade="all, delete-orphan", order_by=CompletedFix.lighthouse_id
    )
