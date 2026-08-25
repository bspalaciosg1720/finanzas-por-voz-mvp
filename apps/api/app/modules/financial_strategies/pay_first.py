import hashlib
import uuid
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.dashboard.service import _month_bounds
from app.modules.financial_health.service import get_financial_health
from app.modules.financial_strategies.models import FinancialStrategyConfig
from app.modules.savings.models import SavingsContribution, SavingsGoal
from app.modules.savings.service import refresh_goal_status
from app.modules.transactions.linked import add_linked_transaction
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


def apply_pay_first(db: Session, user: User, income: Transaction) -> SavingsContribution | None:
    config = db.get(FinancialStrategyConfig, user.id)
    if config is None or not config.pay_first_enabled or config.pay_first_goal_id is None:
        return None
    existing = db.scalar(
        select(SavingsContribution).where(
            SavingsContribution.source_income_transaction_id == income.id,
            SavingsContribution.user_id == user.id,
        )
    )
    if existing is not None:
        return existing
    goal = db.scalar(
        select(SavingsGoal).where(
            SavingsGoal.id == config.pay_first_goal_id,
            SavingsGoal.user_id == user.id,
            SavingsGoal.status == "active",
        )
    )
    if goal is None:
        return None
    local = income.occurred_at.astimezone(ZoneInfo(user.timezone))
    start, end = _month_bounds(local.year, local.month, user.timezone)
    health = get_financial_health(db, user, start=start, end=end)
    safe_capacity = max(
        0,
        health.income_minor
        - health.essential_expense_minor
        - health.minimum_debt_payments_minor
        - health.savings_minor,
    )
    requested = config.pay_first_amount_minor or round(
        income.amount_minor * config.pay_first_percent / 100
    )
    amount = min(requested, safe_capacity)
    if amount <= 0:
        return None
    key = uuid.uuid5(uuid.NAMESPACE_URL, f"pay-first:{user.id}:{income.id}")
    fingerprint = hashlib.sha256(f"pay-first:{income.id}:{goal.id}:{amount}".encode()).hexdigest()
    movement = add_linked_transaction(
        db,
        user,
        movement_type="expense",
        amount_minor=amount,
        occurred_at=income.occurred_at,
        description=f"Págate primero: {goal.name}",
        financial_role="savings_transfer",
        idempotency_key=key,
        idempotency_fingerprint=fingerprint,
    )
    contribution = SavingsContribution(
        goal_id=goal.id,
        user_id=user.id,
        transaction_id=movement.id,
        source_income_transaction_id=income.id,
        amount_minor=amount,
        contributed_at=income.occurred_at,
        note="Aporte automático de Págate primero",
    )
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    refresh_goal_status(db, user, goal.id)
    return contribution
