"""Create debts and debt payments."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0011"
down_revision: str | None = "20260803_0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "debts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("debt_type", sa.String(length=32), nullable=False),
        sa.Column("initial_balance_minor", sa.BigInteger(), nullable=False),
        sa.Column("current_balance_minor", sa.BigInteger(), nullable=False),
        sa.Column("minimum_payment_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("annual_interest_rate_bps", sa.Integer(), nullable=True),
        sa.Column("payment_day", sa.Integer(), nullable=True),
        sa.Column("statement_day", sa.Integer(), nullable=True),
        sa.Column("installment_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_debts_user_id", "debts", ["user_id"])
    op.create_table(
        "debt_payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("debt_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("payment_type", sa.String(length=16), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["debt_id"], ["debts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_debt_payments_debt_id", "debt_payments", ["debt_id"])
    op.create_index("ix_debt_payments_user_id", "debt_payments", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_debt_payments_user_id", table_name="debt_payments")
    op.drop_index("ix_debt_payments_debt_id", table_name="debt_payments")
    op.drop_table("debt_payments")
    op.drop_index("ix_debts_user_id", table_name="debts")
    op.drop_table("debts")
