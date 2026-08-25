from calendar import monthrange
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.modules.categories.models import Category
from app.modules.dashboard.schemas import DashboardSummary, TopExpenseCategory
from app.modules.transactions.accounting import CONSUMPTION_ROLES, EARNED_INCOME_ROLES
from app.modules.transactions.models import Transaction
from app.modules.transactions.schemas import TransactionResponse
from app.modules.users.models import User


def _month_bounds(year: int, month: int, timezone: str) -> tuple[datetime, datetime]:
    zone = ZoneInfo(timezone)
    start = datetime(year, month, 1, tzinfo=zone)
    if month == 12:
        end = datetime(year + 1, 1, 1, tzinfo=zone)
    else:
        end = datetime(year, month + 1, 1, tzinfo=zone)
    return start.astimezone(UTC), end.astimezone(UTC)


def _previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def _totals(
    db: Session,
    user: User,
    start: datetime | None = None,
    end: datetime | None = None,
) -> tuple[int, int]:
    statement = select(
        func.coalesce(
            func.sum(
                case(
                    (
                        (Transaction.type == "income")
                        & Transaction.financial_role.in_(EARNED_INCOME_ROLES),
                        Transaction.amount_minor,
                    ),
                    else_=0,
                )
            ),
            0,
        ),
        func.coalesce(
            func.sum(
                case(
                    (
                        (Transaction.type == "expense")
                        & Transaction.financial_role.in_(CONSUMPTION_ROLES),
                        Transaction.amount_minor,
                    ),
                    else_=0,
                )
            ),
            0,
        ),
    ).where(
        Transaction.user_id == user.id,
        Transaction.currency == user.default_currency,
        Transaction.deleted_at.is_(None),
        Transaction.status == "confirmed",
    )
    if start is not None:
        statement = statement.where(Transaction.occurred_at >= start)
    if end is not None:
        statement = statement.where(Transaction.occurred_at < end)
    income, expense = db.execute(statement).one()
    return int(income), int(expense)


def _cash_balance(db: Session, user: User) -> int:
    income, expense = db.execute(
        select(
            func.coalesce(
                func.sum(case((Transaction.type == "income", Transaction.amount_minor), else_=0)), 0
            ),
            func.coalesce(
                func.sum(case((Transaction.type == "expense", Transaction.amount_minor), else_=0)),
                0,
            ),
        ).where(
            Transaction.user_id == user.id,
            Transaction.currency == user.default_currency,
            Transaction.deleted_at.is_(None),
            Transaction.status == "confirmed",
        )
    ).one()
    return int(income) - int(expense)


def get_dashboard_summary(
    db: Session,
    user: User,
    *,
    year: int,
    month: int,
) -> DashboardSummary:
    monthrange(year, month)
    start, end = _month_bounds(year, month, user.timezone)
    previous_year, previous_month = _previous_month(year, month)
    previous_start, previous_end = _month_bounds(
        previous_year,
        previous_month,
        user.timezone,
    )

    income, expense = _totals(db, user, start, end)
    previous_income, previous_expense = _totals(db, user, previous_start, previous_end)

    top_row = db.execute(
        select(
            Transaction.category_id,
            func.coalesce(Category.name, "Sin categoría"),
            func.sum(Transaction.amount_minor).label("amount_minor"),
        )
        .outerjoin(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user.id,
            Transaction.currency == user.default_currency,
            Transaction.type == "expense",
            Transaction.financial_role.in_(CONSUMPTION_ROLES),
            Transaction.status == "confirmed",
            Transaction.deleted_at.is_(None),
            Transaction.occurred_at >= start,
            Transaction.occurred_at < end,
        )
        .group_by(Transaction.category_id, Category.name)
        .order_by(func.sum(Transaction.amount_minor).desc())
        .limit(1)
    ).one_or_none()

    recent = list(
        db.scalars(
            select(Transaction)
            .where(
                Transaction.user_id == user.id,
                Transaction.currency == user.default_currency,
                Transaction.status == "confirmed",
                Transaction.deleted_at.is_(None),
            )
            .order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
            .limit(5)
        )
    )

    change = (
        round(((expense - previous_expense) / previous_expense) * 100, 1)
        if previous_expense
        else None
    )
    top_category = (
        TopExpenseCategory(
            category_id=str(top_row[0]) if top_row[0] else None,
            name=top_row[1],
            amount_minor=int(top_row[2]),
        )
        if top_row
        else None
    )
    return DashboardSummary(
        currency=user.default_currency,
        period=f"{year:04d}-{month:02d}",
        balance_minor=_cash_balance(db, user),
        income_minor=income,
        expense_minor=expense,
        previous_income_minor=previous_income,
        previous_expense_minor=previous_expense,
        expense_change_percent=change,
        top_expense_category=top_category,
        recent_transactions=[
            TransactionResponse.model_validate(transaction) for transaction in recent
        ],
    )
