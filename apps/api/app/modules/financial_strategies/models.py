import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.shared.time import utc_now


class FinancialStrategyConfig(Base):
    __tablename__ = "financial_strategy_configs"

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    zero_based_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    pay_first_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    pay_first_percent: Mapped[int] = mapped_column(Integer, default=10)
    pay_first_amount_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    pay_first_goal_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("savings_goals.id", ondelete="SET NULL"), nullable=True
    )
    variable_income_budget_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    extraordinary_income_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    extraordinary_debt_percent: Mapped[int] = mapped_column(Integer, default=40)
    extraordinary_savings_percent: Mapped[int] = mapped_column(Integer, default=30)
    extraordinary_goals_percent: Mapped[int] = mapped_column(Integer, default=20)
    extraordinary_personal_percent: Mapped[int] = mapped_column(Integer, default=10)
    hybrid_debt_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    cash_buffer_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    cash_buffer_target_minor: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    no_spend_days_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    no_spend_weekdays: Mapped[str] = mapped_column(String(32), default="")
    purchase_wait_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    purchase_wait_threshold_minor: Mapped[int] = mapped_column(BigInteger, default=200_000)
    purchase_wait_hours: Mapped[int] = mapped_column(Integer, default=24)
    leak_detector_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    opportunity_cost_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
