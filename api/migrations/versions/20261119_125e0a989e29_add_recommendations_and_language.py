from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "125e0a989e29"
down_revision: str | None = "f6adef60d0d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

FAILURE_REASON_CONSTRAINT = "auditfailurereason"
PREVIOUS_FAILURE_REASONS = (
    "queue_unavailable",
    "site_unreachable",
    "pagespeed_quota_exceeded",
    "pagespeed_unavailable",
    "internal_error",
)
FAILURE_REASONS = (*PREVIOUS_FAILURE_REASONS, "recommendations_unavailable")
EXISTING_AUDIT_LANGUAGE = "en"


def _failure_reason_check(reasons: tuple[str, ...]) -> str:
    allowed = ", ".join(f"'{reason}'" for reason in reasons)
    return f"failure_reason IN ({allowed})"


def _replace_failure_reason_constraint(reasons: tuple[str, ...]) -> None:
    op.drop_constraint(FAILURE_REASON_CONSTRAINT, "audits", type_="check")
    op.create_check_constraint(FAILURE_REASON_CONSTRAINT, "audits", _failure_reason_check(reasons))


def upgrade() -> None:
    op.create_table(
        "recommendations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("audit_id", sa.Uuid(), nullable=False),
        sa.Column("rank", sa.SmallInteger(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column(
            "steps",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "impact",
            sa.Enum(
                "high",
                "medium",
                "low",
                name="impact",
                native_enum=False,
                create_constraint=True,
                length=8,
            ),
            nullable=False,
        ),
        sa.Column(
            "effort",
            sa.Enum(
                "low",
                "medium",
                "high",
                name="effort",
                native_enum=False,
                create_constraint=True,
                length=8,
            ),
            nullable=False,
        ),
        sa.Column(
            "devices",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "lighthouse_ids",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["audit_id"], ["audits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("audit_id", "rank"),
    )
    op.add_column(
        "audits",
        sa.Column(
            "language",
            sa.Enum(
                "bs", "en", name="language", native_enum=False, create_constraint=True, length=8
            ),
            nullable=False,
            server_default=EXISTING_AUDIT_LANGUAGE,
        ),
    )
    op.alter_column("audits", "language", server_default=None)
    op.add_column("audits", sa.Column("summary", sa.Text(), nullable=True))
    _replace_failure_reason_constraint(FAILURE_REASONS)


def downgrade() -> None:
    op.execute(
        sa.text(
            "UPDATE audits SET failure_reason = NULL "
            f"WHERE NOT ({_failure_reason_check(PREVIOUS_FAILURE_REASONS)})"
        )
    )
    _replace_failure_reason_constraint(PREVIOUS_FAILURE_REASONS)
    op.drop_column("audits", "summary")
    op.drop_column("audits", "language")
    op.drop_table("recommendations")
