"""Create reminder preferences and idempotent deliveries."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260730_0009"
down_revision: str | None = "20260730_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "reminder_preferences",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("daily_expense_enabled", sa.Boolean(), nullable=False),
        sa.Column("weekly_income_enabled", sa.Boolean(), nullable=False),
        sa.Column("budget_alerts_enabled", sa.Boolean(), nullable=False),
        sa.Column("local_hour", sa.Integer(), nullable=False),
        sa.Column("local_minute", sa.Integer(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "reminder_deliveries",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False),
        sa.Column("period_key", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "kind", "period_key", name="uq_reminder_delivery_period"
        ),
    )
    op.create_index("ix_reminder_deliveries_user_id", "reminder_deliveries", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_reminder_deliveries_user_id", table_name="reminder_deliveries")
    op.drop_table("reminder_deliveries")
    op.drop_table("reminder_preferences")
