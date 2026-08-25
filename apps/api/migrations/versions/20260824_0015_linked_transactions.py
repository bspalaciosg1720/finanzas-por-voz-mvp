"""Link financial domain events to ledger transactions."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0015"
down_revision: str | None = "20260824_0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("financial_role", sa.String(length=24), nullable=False, server_default="regular"),
    )
    for table in (
        "debt_payments",
        "emergency_fund_events",
        "savings_contributions",
        "obligation_payments",
    ):
        op.add_column(table, sa.Column("transaction_id", sa.Uuid(), nullable=True))
        op.create_foreign_key(
            f"fk_{table}_transaction_id",
            table,
            "transactions",
            ["transaction_id"],
            ["id"],
            ondelete="SET NULL",
        )
        op.create_unique_constraint(f"uq_{table}_transaction_id", table, ["transaction_id"])


def downgrade() -> None:
    for table in (
        "obligation_payments",
        "savings_contributions",
        "emergency_fund_events",
        "debt_payments",
    ):
        op.drop_constraint(f"uq_{table}_transaction_id", table, type_="unique")
        op.drop_constraint(f"fk_{table}_transaction_id", table, type_="foreignkey")
        op.drop_column(table, "transaction_id")
    op.drop_column("transactions", "financial_role")
