"""Create emergency funds and events."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0012"
down_revision: str | None = "20260824_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "emergency_funds",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("target_months", sa.Integer(), nullable=False),
        sa.Column("balance_minor", sa.BigInteger(), nullable=False),
        sa.Column("pending_replenishment_minor", sa.BigInteger(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_table(
        "emergency_fund_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=16), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_emergency_fund_events_user_id", "emergency_fund_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_emergency_fund_events_user_id", table_name="emergency_fund_events")
    op.drop_table("emergency_fund_events")
    op.drop_table("emergency_funds")
