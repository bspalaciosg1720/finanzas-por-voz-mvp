import math
import statistics
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.dashboard.service import _month_bounds, _previous_month
from app.modules.financial_health.schemas import IncomeProfileResponse, MonthlyIncome
from app.modules.transactions.accounting import EARNED_INCOME_ROLES
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


def _closed_periods(user: User, months: int) -> list[tuple[int, int]]:
    local_now = datetime.now(ZoneInfo(user.timezone))
    year, month = _previous_month(local_now.year, local_now.month)
    periods = []
    for _ in range(months):
        periods.append((year, month))
        year, month = _previous_month(year, month)
    return list(reversed(periods))


def _lower_quartile(values: list[int]) -> int:
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * 0.25) - 1)
    return ordered[index]


def get_income_profile(db: Session, user: User, *, months: int = 6) -> IncomeProfileResponse:
    monthly = []
    for year, month in _closed_periods(user, months):
        start, end = _month_bounds(year, month, user.timezone)
        amount = int(
            db.scalar(
                select(func.coalesce(func.sum(Transaction.amount_minor), 0)).where(
                    Transaction.user_id == user.id,
                    Transaction.currency == user.default_currency,
                    Transaction.type == "income",
                    Transaction.financial_role.in_(EARNED_INCOME_ROLES),
                    Transaction.status == "confirmed",
                    Transaction.deleted_at.is_(None),
                    Transaction.occurred_at >= start,
                    Transaction.occurred_at < end,
                )
            )
            or 0
        )
        monthly.append(MonthlyIncome(period=f"{year:04d}-{month:02d}", amount_minor=amount))

    observed = [item.amount_minor for item in monthly if item.amount_minor > 0]
    limitations = []
    if len(observed) < 3:
        limitations.append(
            "Se necesitan ingresos en al menos tres meses cerrados para clasificarlos."
        )
        return IncomeProfileResponse(
            currency=user.default_currency,
            classification="insufficient_data",
            months_analyzed=months,
            months_with_income=len(observed),
            average_income_minor=None,
            median_income_minor=None,
            conservative_income_minor=None,
            variability_percent=None,
            monthly_incomes=monthly,
            explanation="Todavía no hay suficientes meses comparables.",
            limitations=limitations,
        )

    average = round(statistics.mean(observed))
    median = round(statistics.median(observed))
    variability = round(statistics.pstdev(observed) * 100 / average, 1) if average else 0.0
    income_range = (max(observed) - min(observed)) / average if average else 0
    variable = variability >= 20 or income_range >= 0.3
    conservative = _lower_quartile(observed) if variable else min(average, median)
    if len(observed) < months:
        limitations.append(
            f"Hay {months - len(observed)} meses sin ingresos registrados; "
            "verifica si faltan datos."
        )
    explanation = (
        "Los ingresos varían de forma relevante. La base conservadora es el cuartil inferior "
        "de los meses con ingresos."
        if variable
        else (
            "Los ingresos son relativamente estables. La base conservadora usa "
            "el menor valor entre promedio y mediana."
        )
    )
    return IncomeProfileResponse(
        currency=user.default_currency,
        classification="variable" if variable else "stable",
        months_analyzed=months,
        months_with_income=len(observed),
        average_income_minor=average,
        median_income_minor=median,
        conservative_income_minor=conservative,
        variability_percent=variability,
        monthly_incomes=monthly,
        explanation=explanation,
        limitations=limitations,
    )
