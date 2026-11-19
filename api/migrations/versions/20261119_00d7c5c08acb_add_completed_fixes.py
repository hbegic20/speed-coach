from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "00d7c5c08acb"
down_revision: str | None = "ae9f0010e687"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "completed_fixes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tracked_site_id", sa.Uuid(), nullable=False),
        sa.Column("lighthouse_id", sa.String(length=128), nullable=False),
        sa.Column(
            "completed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["tracked_site_id"], ["tracked_sites.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tracked_site_id", "lighthouse_id"),
    )


def downgrade() -> None:
    op.drop_table("completed_fixes")
