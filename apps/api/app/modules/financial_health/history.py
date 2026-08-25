from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.financial_health.models import FinancialHealthSnapshot
from app.modules.financial_health.schemas import (
    FinancialHealthSummary,
    HealthHistoryItem,
    HealthHistoryResponse,
)
from app.modules.users.models import User

FORMULA_VERSION = "2.0"


def save_snapshot(db: Session, user: User, summary: FinancialHealthSummary) -> None:
    if summary.score is None:
        return
    year, month = map(int, summary.period.split("-"))
    period = date(year, month, 1)
    snapshot = db.scalar(
        select(FinancialHealthSnapshot).where(
            FinancialHealthSnapshot.user_id == user.id,
            FinancialHealthSnapshot.period == period,
        )
    )
    if snapshot is None:
        snapshot = FinancialHealthSnapshot(user_id=user.id, period=period)
        db.add(snapshot)
    snapshot.score = summary.score
    snapshot.status = summary.status
    snapshot.formula_version = FORMULA_VERSION
    snapshot.components = [item.model_dump() for item in summary.components]
    db.commit()


def get_history(db: Session, user: User, months: int) -> HealthHistoryResponse:
    rows = list(
        db.scalars(
            select(FinancialHealthSnapshot)
            .where(FinancialHealthSnapshot.user_id == user.id)
            .order_by(FinancialHealthSnapshot.period.desc())
            .limit(months)
        )
    )
    rows.reverse()
    items = []
    previous = None
    for row in rows:
        items.append(
            HealthHistoryItem(
                period=row.period.strftime("%Y-%m"),
                score=row.score,
                status=row.status,
                formula_version=row.formula_version,
                change=row.score - previous if previous is not None else None,
            )
        )
        previous = row.score
    change = rows[-1].score - rows[0].score if len(rows) > 1 else 0
    trend = "improving" if change >= 3 else "declining" if change <= -3 else "stable"
    return HealthHistoryResponse(items=items, trend=trend)
