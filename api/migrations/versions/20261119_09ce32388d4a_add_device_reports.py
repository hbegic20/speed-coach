from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "09ce32388d4a"
down_revision: str | None = "964f29592168"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FAILURE_REASON_CONSTRAINT = "auditfailurereason"
PREVIOUS_FAILURE_REASONS = ("queue_unavailable",)
FAILURE_REASONS = (
    "queue_unavailable",
    "site_unreachable",
    "pagespeed_quota_exceeded",
    "pagespeed_unavailable",
    "internal_error",
)


def _failure_reason_check(reasons: tuple[str, ...]) -> str:
    allowed = ", ".join(f"'{reason}'" for reason in reasons)
    return f"failure_reason IN ({allowed})"


def _replace_failure_reason_constraint(reasons: tuple[str, ...]) -> None:
    op.drop_constraint(FAILURE_REASON_CONSTRAINT, "audits", type_="check")
    op.create_check_constraint(FAILURE_REASON_CONSTRAINT, "audits", _failure_reason_check(reasons))


def upgrade() -> None:
    _replace_failure_reason_constraint(FAILURE_REASONS)
    op.create_table(
        "device_reports",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column(
            "device",
            sa.Enum(
                "mobile",
                "desktop",
                name="device",
                native_enum=False,
                create_constraint=True,
                length=16,
            ),
            nullable=False,
        ),
        sa.Column("performance_score", sa.SmallInteger(), nullable=False),
        sa.Column("first_contentful_paint_ms", sa.Double(), nullable=True),
        sa.Column("largest_contentful_paint_ms", sa.Double(), nullable=True),
        sa.Column("total_blocking_time_ms", sa.Double(), nullable=True),
        sa.Column("cumulative_layout_shift", sa.Double(), nullable=True),
        sa.Column("speed_index_ms", sa.Double(), nullable=True),
        sa.Column(
            "findings",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "performance_score BETWEEN 0 AND 100", name="device_reports_performance_score_range"
        ),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("audit_id", "device"),
    )


def downgrade() -> None:
    op.drop_table("device_reports")
    op.execute(
        sa.text(
            "UPDATE audits SET failure_reason = NULL "
            f"WHERE NOT ({_failure_reason_check(PREVIOUS_FAILURE_REASONS)})"
        )
    )
    _replace_failure_reason_constraint(PREVIOUS_FAILURE_REASONS)
