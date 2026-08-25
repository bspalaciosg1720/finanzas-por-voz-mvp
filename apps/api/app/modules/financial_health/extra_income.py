from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.modules.dashboard.service import _month_bounds, _previous_month
from app.modules.financial_health.income import get_income_profile
from app.modules.financial_health.schemas import (
    ExtraIncomeAllocation,
    ExtraIncomeAnalysisResponse,
)
from app.modules.financial_health.service import get_financial_health
from app.modules.users.models import User


def analyze_extra_income(
    db: Session,
    user: User,
    *,
    supplied_amount_minor: int | None = None,
) -> ExtraIncomeAnalysisResponse:
    local_now = datetime.now(ZoneInfo(user.timezone))
    current_start, current_end = _month_bounds(local_now.year, local_now.month, user.timezone)
    current = get_financial_health(db, user, start=current_start, end=current_end)
    profile = get_income_profile(db, user, months=6)
    baseline = profile.conservative_income_minor
    threshold = round(baseline * 0.2) if baseline else None
    automatically_detected = (
        baseline is not None
        and current.income_minor > baseline
        and current.income_minor - baseline >= (threshold or 0)
    )
    extra = (
        supplied_amount_minor
        if supplied_amount_minor is not None
        else current.income_minor - baseline
        if automatically_detected and baseline is not None
        else 0
    )
    source = "supplied" if supplied_amount_minor is not None else "detected"
    limitations = [
        "La propuesta no reserva ni mueve dinero automáticamente.",
        "Confirma que el excedente no esté destinado a necesidades esenciales próximas.",
    ]
    if baseline is None and supplied_amount_minor is None:
        limitations.append("Faltan al menos tres meses de ingresos para detectar un excedente.")
    if not extra:
        return ExtraIncomeAnalysisResponse(
            period=current.period,
            currency=user.default_currency,
            detected=False,
            source=source,
            current_income_minor=current.income_minor,
            conservative_income_minor=baseline,
            extra_income_minor=0,
            applied=False,
            explanation="No se detectó un ingreso al menos 20 % superior a la base conservadora.",
            allocations=[],
            limitations=limitations,
        )

    previous_year, previous_month = _previous_month(local_now.year, local_now.month)
    previous_start, previous_end = _month_bounds(previous_year, previous_month, user.timezone)
    previous = get_financial_health(db, user, start=previous_start, end=previous_end)
    remaining = extra
    allocations: list[ExtraIncomeAllocation] = []

    replenishment = min(remaining, current.pending_replenishment_minor)
    if replenishment:
        allocations.append(
            ExtraIncomeAllocation(
                destination="emergency_replenishment",
                label="Reponer fondo utilizado",
                amount_minor=replenishment,
                rationale="Primero se repone el ahorro de emergencia que ya fue utilizado.",
            )
        )
        remaining -= replenishment

    initial_reserve_gap = max(0, previous.essential_expense_minor - current.emergency_fund_minor)
    reserve = min(remaining, initial_reserve_gap)
    if reserve:
        allocations.append(
            ExtraIncomeAllocation(
                destination="emergency_fund",
                label="Fortalecer reserva inicial",
                amount_minor=reserve,
                rationale="Busca cubrir hasta un mes de gastos esenciales del último mes cerrado.",
            )
        )
        remaining -= reserve

    if remaining and current.total_debt_minor:
        debt_amount = min(current.total_debt_minor, round(remaining * 0.7))
        if debt_amount:
            allocations.append(
                ExtraIncomeAllocation(
                    destination="debt",
                    label="Abono adicional a deuda",
                    amount_minor=debt_amount,
                    rationale="Asigna 70 % del remanente a deuda sin comprometer la reserva.",
                )
            )
            remaining -= debt_amount
    if remaining:
        allocations.append(
            ExtraIncomeAllocation(
                destination="goals",
                label="Ahorro o metas",
                amount_minor=remaining,
                rationale="Conserva el remanente para metas elegidas por el usuario.",
            )
        )

    return ExtraIncomeAnalysisResponse(
        period=current.period,
        currency=user.default_currency,
        detected=True,
        source=source,
        current_income_minor=current.income_minor,
        conservative_income_minor=baseline,
        extra_income_minor=extra,
        applied=False,
        explanation=(
            "El valor fue indicado explícitamente para simular una distribución."
            if supplied_amount_minor is not None
            else "El ingreso recibido supera al menos 20 % la base conservadora calculada."
        ),
        allocations=allocations,
        limitations=limitations,
    )
