import uuid
from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.shared.time import utc_now


class FinancialHealthSnapshot(Base):
    __tablename__ = "financial_health_snapshots"
    __table_args__ = (UniqueConstraint("user_id", "period", name="uq_health_snapshot_period"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    period: Mapped[date] = mapped_column(Date)
    score: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    formula_version: Mapped[str] = mapped_column(String(16))
    components: Mapped[list[dict]] = mapped_column(JSON)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
