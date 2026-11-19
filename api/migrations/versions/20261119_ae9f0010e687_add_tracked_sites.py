from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "ae9f0010e687"
down_revision: str | None = "c574d248244a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TRACKED_SITE_FOREIGN_KEY = "audits_tracked_site_id_fkey"
TRACKED_SITE_INDEX = "ix_audits_tracked_site_id"


def upgrade() -> None:
    op.create_table(
        "tracked_sites",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_key_hash", sa.String(length=64), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_key_hash", "url"),
    )
    op.add_column("audits", sa.Column("tracked_site_id", sa.Uuid(), nullable=True))
    op.create_index(TRACKED_SITE_INDEX, "audits", ["tracked_site_id"])
    op.create_foreign_key(
        TRACKED_SITE_FOREIGN_KEY,
        "audits",
        "tracked_sites",
        ["tracked_site_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(TRACKED_SITE_FOREIGN_KEY, "audits", type_="foreignkey")
    op.drop_index(TRACKED_SITE_INDEX, table_name="audits")
    op.drop_column("audits", "tracked_site_id")
    op.drop_table("tracked_sites")
