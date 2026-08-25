"""Store dismissed deterministic financial alerts."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0017"
down_revision: str | None = "20260824_0016"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_alert_dismissals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("alert_key", sa.String(length=160), nullable=False),
        sa.Column("dismissed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "alert_key", name="uq_financial_alert_dismissal"),
    )
    op.create_index(
        "ix_financial_alert_dismissals_user_id",
        "financial_alert_dismissals",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_financial_alert_dismissals_user_id",
        table_name="financial_alert_dismissals",
    )
    op.drop_table("financial_alert_dismissals")
