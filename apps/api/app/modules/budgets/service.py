import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.budgets.models import Budget
from app.modules.budgets.schemas import BudgetCreate, BudgetResponse, BudgetUpdate
from app.modules.categories.models import Category
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


def month_bounds(user: User, reference: datetime | None = None) -> tuple[datetime, datetime]:
    zone = ZoneInfo(user.timezone)
    local = (reference or datetime.now(UTC)).astimezone(zone)
    start = datetime(local.year, local.month, 1, tzinfo=zone)
    end = (
        datetime(local.year + 1, 1, 1, tzinfo=zone)
        if local.month == 12
        else datetime(local.year, local.month + 1, 1, tzinfo=zone)
    )
    return start.astimezone(UTC), end.astimezone(UTC)


def validate_budget_category(
    db: Session,
    user: User,
    category_id: uuid.UUID,
) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
            Category.movement_scope.in_(("expense", "both")),
            or_(Category.user_id.is_(None), Category.user_id == user.id),
        )
    )
    if category is None:
        raise AppError(
            status=422,
            title="Invalid budget category",
            detail="Choose an active expense category available to this account.",
            error_type="invalid-budget-category",
        )
    return category


def create_budget(db: Session, user: User, payload: BudgetCreate) -> Budget:
    validate_budget_category(db, user, payload.category_id)
    budget = Budget(user_id=user.id, **payload.model_dump())
    db.add(budget)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(
            status=409,
            title="Budget already exists",
            detail="Edit the existing budget for this category and currency.",
            error_type="budget-conflict",
        ) from exc
    db.refresh(budget)
    return budget


def get_budget(db: Session, user: User, budget_id: uuid.UUID) -> Budget:
    budget = db.scalar(
        select(Budget).where(
            Budget.id == budget_id,
            Budget.user_id == user.id,
            Budget.is_active.is_(True),
        )
    )
    if budget is None:
        raise AppError(
            status=404,
            title="Budget not found",
            detail="The requested budget does not exist.",
            error_type="budget-not-found",
        )
    return budget


def update_budget(
    db: Session,
    user: User,
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
) -> Budget:
    budget = get_budget(db, user, budget_id)
    for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(budget, field, value)
    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, user: User, budget_id: uuid.UUID) -> None:
    budget = get_budget(db, user, budget_id)
    budget.is_active = False
    db.commit()


def list_budget_progress(
    db: Session,
    user: User,
    *,
    reference: datetime | None = None,
) -> list[BudgetResponse]:
    start, end = month_bounds(user, reference)
    rows = db.execute(
        select(
            Budget,
            Category.name,
            func.coalesce(func.sum(Transaction.amount_minor), 0),
        )
        .join(Category, Category.id == Budget.category_id)
        .outerjoin(
            Transaction,
            (Transaction.user_id == Budget.user_id)
            & (Transaction.category_id == Budget.category_id)
            & (Transaction.currency == Budget.currency)
            & (Transaction.type == "expense")
            & (Transaction.status == "confirmed")
            & (Transaction.deleted_at.is_(None))
            & (Transaction.occurred_at >= start)
            & (Transaction.occurred_at < end),
        )
        .where(Budget.user_id == user.id, Budget.is_active.is_(True))
        .group_by(Budget.id, Category.name)
        .order_by(Category.name)
    ).all()
    result = []
    for budget, category_name, raw_spent in rows:
        spent = int(raw_spent)
        progress = round((spent / budget.amount_minor) * 100, 1)
        status = (
            "exceeded"
            if progress >= 100
            else "warning"
            if progress >= budget.alert_threshold_percent
            else "on_track"
        )
        result.append(
            BudgetResponse(
                id=budget.id,
                category_id=budget.category_id,
                category_name=category_name,
                amount_minor=budget.amount_minor,
                spent_minor=spent,
                currency=budget.currency,
                alert_threshold_percent=budget.alert_threshold_percent,
                progress_percent=progress,
                alert_status=status,
            )
        )
    return result
