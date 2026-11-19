from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c574d248244a"
down_revision: str | None = "125e0a989e29"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NEW_SCORE_COLUMNS = ("accessibility_score", "best_practices_score", "seo_score")


def _range_constraint(column: str) -> str:
    return f"device_reports_{column}_range"


def upgrade() -> None:
    for column in NEW_SCORE_COLUMNS:
        op.add_column("device_reports", sa.Column(column, sa.SmallInteger(), nullable=True))
        op.create_check_constraint(
            _range_constraint(column), "device_reports", f"{column} BETWEEN 0 AND 100"
        )


def downgrade() -> None:
    for column in reversed(NEW_SCORE_COLUMNS):
        op.drop_constraint(_range_constraint(column), "device_reports", type_="check")
        op.drop_column("device_reports", column)
