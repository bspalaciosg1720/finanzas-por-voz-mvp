"""Add inbound email addresses and transaction suggestions."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260803_0010"
down_revision: str | None = "20260730_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "inbound_email_addresses",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("token", sa.String(length=48), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
        sa.UniqueConstraint("token"),
    )
    op.create_table(
        "transaction_suggestions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("transaction_id", sa.Uuid(), nullable=True),
        sa.Column("message_hash", sa.String(length=64), nullable=False),
        sa.Column("sender_domain", sa.String(length=180), nullable=False),
        sa.Column("type", sa.String(length=16), nullable=False),
        sa.Column("amount_minor", sa.BigInteger(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.String(length=240), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["transaction_id"], ["transactions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "message_hash", name="uq_suggestion_user_message"),
    )
    op.create_index("ix_transaction_suggestions_user_id", "transaction_suggestions", ["user_id"])
    op.create_index(
        "ix_suggestions_user_status_created",
        "transaction_suggestions",
        ["user_id", "status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_suggestions_user_status_created", table_name="transaction_suggestions")
    op.drop_index("ix_transaction_suggestions_user_id", table_name="transaction_suggestions")
    op.drop_table("transaction_suggestions")
    op.drop_table("inbound_email_addresses")
