"""Create financial obligations and payments."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0013"
down_revision: str | None = "20260824_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_obligations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("obligation_type", sa.String(length=24), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("due_day", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_financial_obligations_user_id", "financial_obligations", ["user_id"])
    op.create_table(
        "obligation_payments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("obligation_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(
            ["obligation_id"], ["financial_obligations.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("obligation_id", "due_date", name="uq_obligation_due_payment"),
    )
    op.create_index(
        "ix_obligation_payments_obligation_id", "obligation_payments", ["obligation_id"]
    )
    op.create_index("ix_obligation_payments_user_id", "obligation_payments", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_obligation_payments_user_id", table_name="obligation_payments")
    op.drop_index("ix_obligation_payments_obligation_id", table_name="obligation_payments")
    op.drop_table("obligation_payments")
    op.drop_index("ix_financial_obligations_user_id", table_name="financial_obligations")
    op.drop_table("financial_obligations")
