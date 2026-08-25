import uuid
from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.shared.time import utc_now


class FinancialObligation(Base):
    __tablename__ = "financial_obligations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    obligation_type: Mapped[str] = mapped_column(String(24))
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    due_day: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)


class ObligationPayment(Base):
    __tablename__ = "obligation_payments"
    __table_args__ = (
        UniqueConstraint("obligation_id", "due_date", name="uq_obligation_due_payment"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    obligation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("financial_obligations.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("transactions.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    due_date: Mapped[date] = mapped_column(Date)
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    amount_minor: Mapped[int] = mapped_column(BigInteger)
