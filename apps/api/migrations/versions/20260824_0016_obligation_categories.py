"""Add category snapshots to obligations and their payments."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0016"
down_revision: str | None = "20260824_0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("financial_obligations", sa.Column("category_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_financial_obligations_category_id",
        "financial_obligations",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_financial_obligations_category_id", "financial_obligations", ["category_id"]
    )
    op.add_column("obligation_payments", sa.Column("category_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_obligation_payments_category_id",
        "obligation_payments",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_obligation_payments_category_id", "obligation_payments", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_obligation_payments_category_id", table_name="obligation_payments")
    op.drop_constraint(
        "fk_obligation_payments_category_id", "obligation_payments", type_="foreignkey"
    )
    op.drop_column("obligation_payments", "category_id")
    op.drop_index("ix_financial_obligations_category_id", table_name="financial_obligations")
    op.drop_constraint(
        "fk_financial_obligations_category_id",
        "financial_obligations",
        type_="foreignkey",
    )
    op.drop_column("financial_obligations", "category_id")
