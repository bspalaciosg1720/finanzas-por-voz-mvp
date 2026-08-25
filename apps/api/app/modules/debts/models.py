import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.shared.time import utc_now


class Debt(Base):
    __tablename__ = "debts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80))
    debt_type: Mapped[str] = mapped_column(String(32))
    initial_balance_minor: Mapped[int] = mapped_column(BigInteger)
    current_balance_minor: Mapped[int] = mapped_column(BigInteger)
    minimum_payment_minor: Mapped[int] = mapped_column(BigInteger)
    currency: Mapped[str] = mapped_column(String(3))
    annual_interest_rate_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    statement_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    installment_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )


class DebtPayment(Base):
    __tablename__ = "debt_payments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    debt_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("debts.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("transactions.id", ondelete="SET NULL"), unique=True, nullable=True
    )
    amount_minor: Mapped[int] = mapped_column(BigInteger)
    payment_type: Mapped[str] = mapped_column(String(16))
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    note: Mapped[str] = mapped_column(String(120), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
