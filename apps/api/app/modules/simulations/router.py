from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.dashboard.service import _month_bounds
from app.modules.debts.service import payoff_plan
from app.modules.financial_health.service import get_financial_health
from app.modules.simulations.schemas import ScenarioValues, SimulationRequest, SimulationResponse

router = APIRouter(prefix="/simulations", tags=["Simulations"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=SimulationResponse)
def simulate(payload: SimulationRequest, user: CurrentUser, db: DbSession):
    now = datetime.now(ZoneInfo(user.timezone))
    start, end = _month_bounds(now.year, now.month, user.timezone)
    health = get_financial_health(db, user, start=start, end=end)
    current = ScenarioValues(
        available_cash_minor=health.available_cash_minor,
        variable_expense_minor=health.variable_expense_minor,
        savings_minor=health.savings_minor,
    )
    simulated = current.model_copy(deep=True)
    limitations = []
    if payload.scenario == "reduce_variable":
        reduction = min(payload.amount_minor, simulated.variable_expense_minor)
        simulated.variable_expense_minor -= reduction
        simulated.available_cash_minor += reduction
    elif payload.scenario == "increase_income":
        simulated.available_cash_minor += payload.amount_minor
    elif payload.scenario == "increase_savings":
        simulated.savings_minor += payload.amount_minor
        simulated.available_cash_minor -= payload.amount_minor
    elif payload.scenario == "savings_goal":
        simulated.monthly_goal_amount_minor = (
            payload.amount_minor + payload.months - 1
        ) // payload.months
    else:
        simulated.available_cash_minor -= payload.amount_minor
        plan = payoff_plan(db, user, strategy="avalanche", extra_payment_minor=payload.amount_minor)
        simulated.debt_free_months = plan.estimated_months
        simulated.debt_interest_minor = plan.estimated_interest_minor
        limitations.extend(plan.limitations)
    return SimulationResponse(
        scenario=payload.scenario,
        currency=user.default_currency,
        current=current,
        simulated=simulated,
        limitations=limitations,
    )
