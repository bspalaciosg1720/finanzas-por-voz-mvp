from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.categories.models import Category
from app.modules.dashboard.service import _month_bounds, _previous_month
from app.modules.financial_health.schemas import FinancialPattern, FinancialPatternsResponse
from app.modules.savings.models import SavingsContribution
from app.modules.transactions.accounting import CONSUMPTION_ROLES, EARNED_INCOME_ROLES
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


def _change(previous: int, current: int) -> float | None:
    return round((current - previous) * 100 / previous, 1) if previous else None


def _periods(user: User, months: int) -> list[tuple[int, int]]:
    local_now = datetime.now(ZoneInfo(user.timezone))
    year, month = _previous_month(local_now.year, local_now.month)
    result = []
    for _ in range(months):
        result.append((year, month))
        year, month = _previous_month(year, month)
    return list(reversed(result))


def detect_patterns(db: Session, user: User, *, months: int = 3) -> FinancialPatternsResponse:
    periods = _periods(user, months)
    labels = [f"{year:04d}-{month:02d}" for year, month in periods]
    expenses: list[int] = []
    incomes: list[int] = []
    savings: list[int] = []
    for year, month in periods:
        start, end = _month_bounds(year, month, user.timezone)
        expense, income = db.execute(
            select(
                func.coalesce(
                    func.sum(Transaction.amount_minor).filter(
                        Transaction.type == "expense",
                        Transaction.financial_role.in_(CONSUMPTION_ROLES),
                    ),
                    0,
                ),
                func.coalesce(
                    func.sum(Transaction.amount_minor).filter(
                        Transaction.type == "income",
                        Transaction.financial_role.in_(EARNED_INCOME_ROLES),
                    ),
                    0,
                ),
            ).where(
                Transaction.user_id == user.id,
                Transaction.currency == user.default_currency,
                Transaction.status == "confirmed",
                Transaction.deleted_at.is_(None),
                Transaction.occurred_at >= start,
                Transaction.occurred_at < end,
            )
        ).one()
        expenses.append(int(expense))
        incomes.append(int(income))
        savings.append(
            int(
                db.scalar(
                    select(func.coalesce(func.sum(SavingsContribution.amount_minor), 0)).where(
                        SavingsContribution.user_id == user.id,
                        SavingsContribution.contributed_at >= start,
                        SavingsContribution.contributed_at < end,
                    )
                )
                or 0
            )
        )

    found: list[FinancialPattern] = []
    if all(value > 0 for value in expenses) and all(
        current > previous for previous, current in zip(expenses, expenses[1:], strict=False)
    ):
        change = _change(expenses[0], expenses[-1])
        if change is not None and change >= 15:
            found.append(
                FinancialPattern(
                    key="expense_growth",
                    direction="attention",
                    title="Tus gastos vienen aumentando",
                    detail=f"El gasto total subió {change} % entre {labels[0]} y {labels[-1]}.",
                    start_period=labels[0],
                    end_period=labels[-1],
                    previous_amount_minor=expenses[0],
                    current_amount_minor=expenses[-1],
                    change_percent=change,
                )
            )
    if savings[0] > 0 and all(
        current < previous for previous, current in zip(savings, savings[1:], strict=False)
    ):
        change = _change(savings[0], savings[-1])
        if change is not None and change <= -15:
            found.append(
                FinancialPattern(
                    key="savings_decline",
                    direction="attention",
                    title="Tu ahorro viene disminuyendo",
                    detail=f"Los aportes bajaron {abs(change)} % entre {labels[0]} y {labels[-1]}.",
                    start_period=labels[0],
                    end_period=labels[-1],
                    previous_amount_minor=savings[0],
                    current_amount_minor=savings[-1],
                    change_percent=change,
                )
            )
    deficit_count = sum(
        income > 0 and expense > income for income, expense in zip(incomes, expenses, strict=True)
    )
    if deficit_count >= 2:
        found.append(
            FinancialPattern(
                key="recurrent_deficit",
                direction="attention",
                title="Hay déficit frecuente",
                detail=(
                    f"Los gastos superaron los ingresos en {deficit_count} "
                    f"de {months} meses cerrados."
                ),
                start_period=labels[0],
                end_period=labels[-1],
            )
        )

    previous_start, previous_end = _month_bounds(*periods[-2], user.timezone)
    current_start, current_end = _month_bounds(*periods[-1], user.timezone)

    def category_totals(start: datetime, end: datetime) -> dict[object, tuple[str, int]]:
        rows = db.execute(
            select(Transaction.category_id, Category.name, func.sum(Transaction.amount_minor))
            .join(Category, Category.id == Transaction.category_id)
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
        ).all()
        return {category_id: (name, int(amount)) for category_id, name, amount in rows}

    previous_categories = category_totals(previous_start, previous_end)
    current_categories = category_totals(current_start, current_end)
    candidates = []
    for category_id, (name, previous) in previous_categories.items():
        current = current_categories.get(category_id, (name, 0))[1]
        change = _change(previous, current)
        if previous > 0 and change is not None and change >= 20:
            candidates.append((change, name, previous, current))
    if candidates:
        change, name, previous, current = max(candidates)
        found.append(
            FinancialPattern(
                key="category_growth",
                direction="attention",
                title=f"Aumentó el gasto en {name}",
                detail=f"Esta categoría creció {change} % de {labels[-2]} a {labels[-1]}.",
                start_period=labels[-2],
                end_period=labels[-1],
                previous_amount_minor=previous,
                current_amount_minor=current,
                change_percent=change,
                category_name=name,
            )
        )

    non_empty_months = sum(
        bool(income or expense or saving)
        for income, expense, saving in zip(incomes, expenses, savings, strict=True)
    )
    limitations = []
    if non_empty_months < months:
        limitations.append(
            f"Solo {non_empty_months} de {months} meses tienen datos; "
            "los patrones pueden ser incompletos."
        )
    limitations.append(
        "El crecimiento histórico de deuda requiere instantáneas mensuales y todavía "
        "no se infiere de saldos actuales."
    )
    return FinancialPatternsResponse(
        currency=user.default_currency,
        months_analyzed=months,
        periods=labels,
        patterns=found[:4],
        limitations=limitations,
    )
