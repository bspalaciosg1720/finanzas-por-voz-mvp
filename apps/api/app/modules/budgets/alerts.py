import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.budgets.models import Budget, BudgetAlert
from app.modules.budgets.schemas import BudgetAlertResponse
from app.modules.categories.models import Category
from app.modules.transactions.models import Transaction
from app.modules.users.models import User
from app.shared.time import utc_now


def evaluate_budget_alert(
    db: Session,
    user: User,
    *,
    category_id: uuid.UUID | None,
    currency: str,
    occurred_at: datetime,
) -> None:
    if category_id is None:
        return
    budget = db.scalar(
        select(Budget).where(
            Budget.user_id == user.id,
            Budget.category_id == category_id,
            Budget.currency == currency,
            Budget.is_active.is_(True),
        )
    )
    if budget is None:
        return

    zone = ZoneInfo(user.timezone)
    local = occurred_at.astimezone(zone)
    period_start = local.date().replace(day=1)
    start = datetime(local.year, local.month, 1, tzinfo=zone)
    end = (
        datetime(local.year + 1, 1, 1, tzinfo=zone)
        if local.month == 12
        else datetime(local.year, local.month + 1, 1, tzinfo=zone)
    )
    spent = int(
        db.scalar(
            select(func.coalesce(func.sum(Transaction.amount_minor), 0)).where(
                Transaction.user_id == user.id,
                Transaction.category_id == category_id,
                Transaction.currency == currency,
                Transaction.type == "expense",
                Transaction.status == "confirmed",
                Transaction.deleted_at.is_(None),
                Transaction.occurred_at >= start,
                Transaction.occurred_at < end,
            )
        )
        or 0
    )
    progress = (spent / budget.amount_minor) * 100
    level = (
        "exceeded"
        if progress >= 100
        else "warning"
        if progress >= budget.alert_threshold_percent
        else None
    )
    if level is None:
        return
    db.add(
        BudgetAlert(
            user_id=user.id,
            budget_id=budget.id,
            period_start=period_start,
            level=level,
        )
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()


def mark_alert_read(
    db: Session,
    user: User,
    alert_id: uuid.UUID,
) -> BudgetAlert:
    alert = db.scalar(
        select(BudgetAlert).where(
            BudgetAlert.id == alert_id,
            BudgetAlert.user_id == user.id,
        )
    )
    if alert is None:
        raise AppError(
            status=404,
            title="Budget alert not found",
            detail="The requested alert does not exist.",
            error_type="budget-alert-not-found",
        )
    if alert.read_at is None:
        alert.read_at = utc_now()
        db.commit()
        db.refresh(alert)
    return alert


def list_alerts(
    db: Session,
    user: User,
    *,
    unread_only: bool,
) -> list[BudgetAlertResponse]:
    statement = (
        select(BudgetAlert, Category.name)
        .join(Budget, Budget.id == BudgetAlert.budget_id)
        .join(Category, Category.id == Budget.category_id)
        .where(BudgetAlert.user_id == user.id)
    )
    if unread_only:
        statement = statement.where(BudgetAlert.read_at.is_(None))
    rows = db.execute(statement.order_by(BudgetAlert.created_at.desc())).all()
    return [
        BudgetAlertResponse(
            id=alert.id,
            budget_id=alert.budget_id,
            period_start=alert.period_start,
            level=alert.level,
            category_name=category_name,
            read_at=alert.read_at,
            created_at=alert.created_at,
        )
        for alert, category_name in rows
    ]
