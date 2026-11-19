from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f6adef60d0d3"
down_revision: str | None = "09ce32388d4a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "audits",
        sa.Column(
            "platform",
            sa.Enum(
                "wordpress",
                "shopify",
                "wix",
                "squarespace",
                "webflow",
                "joomla",
                "drupal",
                "nextjs",
                "nuxt",
                "unknown",
                name="platform",
                native_enum=False,
                create_constraint=True,
                length=16,
            ),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("audits", "platform")
