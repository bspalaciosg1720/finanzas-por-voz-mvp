"""Create versioned financial health history."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260824_0014"
down_revision: str | None = "20260824_0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "financial_health_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("period", sa.Date(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("formula_version", sa.String(length=16), nullable=False),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "period", name="uq_health_snapshot_period"),
    )
    op.create_index(
        "ix_financial_health_snapshots_user_id", "financial_health_snapshots", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_financial_health_snapshots_user_id", table_name="financial_health_snapshots")
    op.drop_table("financial_health_snapshots")
