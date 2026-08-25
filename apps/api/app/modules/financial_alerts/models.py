import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.database import Base
from app.shared.time import utc_now


class FinancialAlertDismissal(Base):
    __tablename__ = "financial_alert_dismissals"
    __table_args__ = (
        UniqueConstraint("user_id", "alert_key", name="uq_financial_alert_dismissal"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    alert_key: Mapped[str] = mapped_column(String(160))
    dismissed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
