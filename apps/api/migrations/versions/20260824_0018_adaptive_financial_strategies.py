"""Add adaptive strategy configuration and sinking fund fields."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0018"
down_revision: str | None = "20260824_0017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "savings_goals",
        sa.Column("goal_type", sa.String(length=24), nullable=False, server_default="general"),
    )
    op.add_column(
        "savings_goals", sa.Column("planned_monthly_minor", sa.BigInteger(), nullable=True)
    )
    op.add_column(
        "savings_contributions",
        sa.Column("source_income_transaction_id", sa.Uuid(), nullable=True),
    )
    op.create_foreign_key(
        "fk_savings_contributions_source_income",
        "savings_contributions",
        "transactions",
        ["source_income_transaction_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_unique_constraint(
        "uq_savings_contributions_source_income",
        "savings_contributions",
        ["source_income_transaction_id"],
    )
    op.create_table(
        "financial_strategy_configs",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("zero_based_enabled", sa.Boolean(), nullable=False),
        sa.Column("pay_first_enabled", sa.Boolean(), nullable=False),
        sa.Column("pay_first_percent", sa.Integer(), nullable=False),
        sa.Column("pay_first_amount_minor", sa.BigInteger(), nullable=True),
        sa.Column("pay_first_goal_id", sa.Uuid(), nullable=True),
        sa.Column("variable_income_budget_enabled", sa.Boolean(), nullable=False),
        sa.Column("extraordinary_income_enabled", sa.Boolean(), nullable=False),
        sa.Column("extraordinary_debt_percent", sa.Integer(), nullable=False),
        sa.Column("extraordinary_savings_percent", sa.Integer(), nullable=False),
        sa.Column("extraordinary_goals_percent", sa.Integer(), nullable=False),
        sa.Column("extraordinary_personal_percent", sa.Integer(), nullable=False),
        sa.Column("hybrid_debt_enabled", sa.Boolean(), nullable=False),
        sa.Column("cash_buffer_enabled", sa.Boolean(), nullable=False),
        sa.Column("cash_buffer_target_minor", sa.BigInteger(), nullable=True),
        sa.Column("no_spend_days_enabled", sa.Boolean(), nullable=False),
        sa.Column("no_spend_weekdays", sa.String(length=32), nullable=False),
        sa.Column("purchase_wait_enabled", sa.Boolean(), nullable=False),
        sa.Column("purchase_wait_threshold_minor", sa.BigInteger(), nullable=False),
        sa.Column("purchase_wait_hours", sa.Integer(), nullable=False),
        sa.Column("leak_detector_enabled", sa.Boolean(), nullable=False),
        sa.Column("opportunity_cost_enabled", sa.Boolean(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pay_first_goal_id"], ["savings_goals.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("financial_strategy_configs")
    op.drop_constraint(
        "uq_savings_contributions_source_income",
        "savings_contributions",
        type_="unique",
    )
    op.drop_constraint(
        "fk_savings_contributions_source_income",
        "savings_contributions",
        type_="foreignkey",
    )
    op.drop_column("savings_contributions", "source_income_transaction_id")
    op.drop_column("savings_goals", "planned_monthly_minor")
    op.drop_column("savings_goals", "goal_type")
