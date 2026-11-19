import uuid
from enum import StrEnum

from sqlalchemy import JSON, ForeignKey, SmallInteger, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, string_enum


class Impact(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Effort(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def _json_list() -> JSON:
    return JSON().with_variant(JSONB, "postgresql")


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("audit_id", "rank"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    audit_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("audits.id", ondelete="CASCADE"))
    rank: Mapped[int] = mapped_column(SmallInteger)
    title: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    steps: Mapped[list[str]] = mapped_column(_json_list())
    impact: Mapped[Impact] = mapped_column(string_enum(Impact, 8))
    effort: Mapped[Effort] = mapped_column(string_enum(Effort, 8))
    devices: Mapped[list[str]] = mapped_column(_json_list())
    lighthouse_ids: Mapped[list[str]] = mapped_column(_json_list())
