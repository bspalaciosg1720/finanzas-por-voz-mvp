from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.modules.budgets.service import list_budget_progress
from app.modules.debts.models import Debt
from app.modules.financial_alerts.models import FinancialAlertDismissal
from app.modules.financial_alerts.schemas import FinancialAlert, FinancialAlertsResponse
from app.modules.financial_calendar.service import calendar_view
from app.modules.financial_health.patterns import detect_patterns
from app.modules.users.models import User


def get_alerts(db: Session, user: User, *, limit: int = 3) -> FinancialAlertsResponse:
    today = datetime.now(ZoneInfo(user.timezone)).date()
    candidates: list[FinancialAlert] = []
    for item in calendar_view(db, user, today=today, days=7).items:
        if item.status == "paid" or item.days_until_due > 3:
            continue
        when = "vence hoy" if item.days_until_due == 0 else f"vence en {item.days_until_due} días"
        candidates.append(
            FinancialAlert(
                key=f"due:{item.obligation_id}:{item.due_date.isoformat()}",
                kind="upcoming_payment",
                priority=1,
                tone="attention",
                title=f"{item.name} {when}",
                detail=f"Pago previsto por {item.amount_minor} {item.currency}.",
                action_path="/(app)/planning",
            )
        )
    for budget in list_budget_progress(db, user):
        if budget.alert_status not in {"warning", "exceeded"}:
            continue
        candidates.append(
            FinancialAlert(
                key=f"budget:{budget.id}:{today:%Y-%m}:{budget.alert_status}",
                kind="budget",
                priority=1 if budget.alert_status == "exceeded" else 2,
                tone="attention",
                title=(
                    f"Presupuesto excedido: {budget.category_name}"
                    if budget.alert_status == "exceeded"
                    else f"Presupuesto en alerta: {budget.category_name}"
                ),
                detail=f"Has utilizado {budget.progress_percent} % del valor planeado.",
                action_path="/(app)/budget",
            )
        )
    for pattern in detect_patterns(db, user, months=3).patterns:
        candidates.append(
            FinancialAlert(
                key=f"pattern:{pattern.key}:{pattern.end_period}",
                kind="pattern",
                priority=2,
                tone=pattern.direction,
                title=pattern.title,
                detail=pattern.detail,
                action_path="/(app)/health",
            )
        )
    debts = db.scalars(
        select(Debt).where(
            Debt.user_id == user.id,
            Debt.currency == user.default_currency,
            Debt.status == "active",
            Debt.initial_balance_minor > 0,
        )
    )
    for debt in debts:
        remaining_percent = round(debt.current_balance_minor * 100 / debt.initial_balance_minor, 1)
        if remaining_percent <= 15:
            candidates.append(
                FinancialAlert(
                    key=f"debt-near:{debt.id}:{int(round(remaining_percent * 10))}",
                    kind="debt_progress",
                    priority=3,
                    tone="positive",
                    title=f"Estás cerca de terminar {debt.name}",
                    detail=f"Falta aproximadamente el {remaining_percent} % del saldo inicial.",
                    action_path="/(app)/debts",
                )
            )
    dismissed = set(
        db.scalars(
            select(FinancialAlertDismissal.alert_key).where(
                FinancialAlertDismissal.user_id == user.id
            )
        )
    )
    unique = {item.key: item for item in candidates if item.key not in dismissed}
    ordered = sorted(unique.values(), key=lambda item: (item.priority, item.key))
    return FinancialAlertsResponse(items=ordered[:limit], total_candidates=len(ordered))


def dismiss_alert(db: Session, user: User, key: str) -> None:
    existing = db.scalar(
        select(FinancialAlertDismissal).where(
            FinancialAlertDismissal.user_id == user.id,
            FinancialAlertDismissal.alert_key == key,
        )
    )
    if existing is not None:
        return
    db.add(FinancialAlertDismissal(user_id=user.id, alert_key=key))
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
