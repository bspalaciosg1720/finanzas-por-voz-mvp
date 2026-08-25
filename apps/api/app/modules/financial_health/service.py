from datetime import UTC, datetime

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.modules.budgets.models import Budget
from app.modules.categories.models import Category
from app.modules.debts.models import Debt, DebtPayment
from app.modules.emergency_fund.models import EmergencyFund, EmergencyFundEvent
from app.modules.financial_calendar.models import FinancialObligation, ObligationPayment
from app.modules.financial_health.classification import ESSENTIAL_SLUGS
from app.modules.financial_health.engine import (
    HealthInputs,
    calculate_components,
    normalized_score,
    score_status,
)
from app.modules.financial_health.schemas import FinancialHealthSummary, HealthRecommendation
from app.modules.savings.models import SavingsContribution
from app.modules.transactions.accounting import CONSUMPTION_ROLES, EARNED_INCOME_ROLES
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


def get_financial_health(
    db: Session, user: User, *, start: datetime, end: datetime
) -> FinancialHealthSummary:
    rows = db.execute(
        select(Category.slug, func.sum(Transaction.amount_minor))
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
        .group_by(Category.slug)
    ).all()
    essential = variable = unclassified = 0
    for slug, amount in rows:
        if slug is None:
            unclassified += int(amount)
        elif slug in ESSENTIAL_SLUGS:
            essential += int(amount)
        else:
            variable += int(amount)

    income = int(
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
    savings = int(
        db.scalar(
            select(func.coalesce(func.sum(SavingsContribution.amount_minor), 0)).where(
                SavingsContribution.user_id == user.id,
                SavingsContribution.contributed_at >= start,
                SavingsContribution.contributed_at < end,
            )
        )
        or 0
    )
    active_budgets = list(
        db.scalars(
            select(Budget).where(
                Budget.user_id == user.id,
                Budget.currency == user.default_currency,
                Budget.is_active.is_(True),
            )
        )
    )
    budget_total = sum(item.amount_minor for item in active_budgets)
    category_ids = [item.category_id for item in active_budgets]
    budget_spent = (
        int(
            db.scalar(
                select(func.coalesce(func.sum(Transaction.amount_minor), 0)).where(
                    Transaction.user_id == user.id,
                    Transaction.currency == user.default_currency,
                    Transaction.category_id.in_(category_ids),
                    Transaction.type == "expense",
                    Transaction.status == "confirmed",
                    Transaction.deleted_at.is_(None),
                    Transaction.occurred_at >= start,
                    Transaction.occurred_at < end,
                )
            )
            or 0
        )
        if category_ids
        else 0
    )
    debt_total, minimum_debt_payments = db.execute(
        select(
            func.coalesce(func.sum(Debt.current_balance_minor), 0),
            func.coalesce(func.sum(Debt.minimum_payment_minor), 0),
        ).where(
            Debt.user_id == user.id,
            Debt.currency == user.default_currency,
            Debt.status == "active",
        )
    ).one()
    debt_payments = int(
        db.scalar(
            select(func.coalesce(func.sum(DebtPayment.amount_minor), 0)).where(
                DebtPayment.user_id == user.id,
                DebtPayment.paid_at >= start,
                DebtPayment.paid_at < end,
            )
        )
        or 0
    )
    fund_deposits, fund_withdrawals = db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (
                            EmergencyFundEvent.event_type == "deposit",
                            EmergencyFundEvent.amount_minor,
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
                            EmergencyFundEvent.event_type == "withdrawal",
                            EmergencyFundEvent.amount_minor,
                        ),
                        else_=0,
                    )
                ),
                0,
            ),
        ).where(
            EmergencyFundEvent.user_id == user.id,
            EmergencyFundEvent.occurred_at >= start,
            EmergencyFundEvent.occurred_at < end,
        )
    ).one()
    emergency_fund = db.get(EmergencyFund, user.id)
    emergency_balance = emergency_fund.balance_minor if emergency_fund else 0
    pending_replenishment = emergency_fund.pending_replenishment_minor if emergency_fund else 0
    obligations_due = int(
        db.scalar(
            select(func.count(FinancialObligation.id)).where(
                FinancialObligation.user_id == user.id,
                FinancialObligation.currency == user.default_currency,
                FinancialObligation.is_active.is_(True),
            )
        )
        or 0
    )
    obligations_paid = int(
        db.scalar(
            select(func.count(ObligationPayment.id)).where(
                ObligationPayment.user_id == user.id,
                ObligationPayment.due_date >= start.date(),
                ObligationPayment.due_date < end.date(),
            )
        )
        or 0
    )
    values = HealthInputs(
        income,
        essential,
        variable,
        unclassified,
        savings,
        budget_total,
        budget_spent,
        int(debt_total),
        int(minimum_debt_payments),
        emergency_balance,
        obligations_due,
        obligations_paid,
    )
    components = calculate_components(values)
    score = normalized_score(components)
    total_expense = essential + variable + unclassified
    limitations = []
    if income == 0:
        limitations.append("Registra al menos un ingreso del mes para calcular tu puntuación.")
    if unclassified:
        limitations.append("Hay gastos sin categoría; clasificarlos hará más preciso el análisis.")
    if not debt_total:
        limitations.append("No hay deudas activas registradas para evaluar endeudamiento.")
    if essential == 0:
        limitations.append(
            "Registra gastos esenciales para calcular la cobertura del fondo de emergencia."
        )
    recommendations: list[HealthRecommendation] = []
    if income and total_expense > income:
        recommendations.append(
            HealthRecommendation(
                priority=1,
                title="Protege tu flujo de caja",
                detail=(
                    f"Tus gastos superan tus ingresos por {total_expense - income} "
                    "en la moneda de tu cuenta."
                ),
            )
        )
    if unclassified:
        recommendations.append(
            HealthRecommendation(
                priority=2,
                title="Clasifica tus movimientos",
                detail=(
                    "Revisa los gastos sin categoría para distinguir necesidades "
                    "de gastos variables."
                ),
            )
        )
    if income and savings == 0:
        recommendations.append(
            HealthRecommendation(
                priority=3,
                title="Empieza con un ahorro alcanzable",
                detail="Registra un aporte a una meta cuando tu flujo disponible lo permita.",
            )
        )
    coverage = emergency_balance / essential if essential else None
    if coverage is not None and coverage < 1:
        recommendations.append(
            HealthRecommendation(
                priority=2,
                title="Construye una reserva inicial",
                detail=(
                    "Tu fondo cubre menos de un mes de gastos esenciales. Empieza "
                    "con un aporte que no comprometa tus necesidades básicas."
                ),
            )
        )
    if pending_replenishment:
        recommendations.append(
            HealthRecommendation(
                priority=2,
                title="Repón el ahorro utilizado",
                detail=(
                    f"Tienes {pending_replenishment} pendientes por reponer en tu "
                    "fondo de emergencia."
                ),
            )
        )
    if income and minimum_debt_payments / income > 0.3:
        recommendations.append(
            HealthRecommendation(
                priority=1,
                title="Revisa la carga de tus deudas",
                detail=(
                    "Tus pagos mínimos superan el 30 % de tus ingresos. Conserva "
                    "primero el dinero para necesidades esenciales."
                ),
            )
        )
    if not recommendations and income:
        recommendations.append(
            HealthRecommendation(
                priority=4,
                title="Mantén el seguimiento",
                detail=(
                    "Tus registros permiten ver el mes con claridad. Revisa el avance "
                    "de tus presupuestos cada semana."
                ),
            )
        )

    def ratio(amount: int) -> float | None:
        return round(amount * 100 / income, 1) if income else None

    return FinancialHealthSummary(
        period=start.astimezone(UTC).strftime("%Y-%m"),
        currency=user.default_currency,
        score=score,
        status=score_status(score),
        confidence="media" if unclassified else "alta" if income else "baja",
        income_minor=income,
        essential_expense_minor=essential,
        variable_expense_minor=variable,
        unclassified_expense_minor=unclassified,
        total_expense_minor=total_expense,
        available_cash_minor=(
            income
            - total_expense
            - debt_payments
            - savings
            - int(fund_deposits)
            + int(fund_withdrawals)
        ),
        savings_minor=savings,
        total_debt_minor=int(debt_total),
        minimum_debt_payments_minor=int(minimum_debt_payments),
        debt_payments_minor=debt_payments,
        emergency_fund_minor=emergency_balance,
        emergency_fund_months=round(coverage, 2) if coverage is not None else None,
        pending_replenishment_minor=pending_replenishment,
        essential_percent=ratio(essential),
        variable_percent=ratio(variable),
        savings_percent=ratio(savings),
        debt_payment_percent=ratio(int(minimum_debt_payments)),
        budget_used_percent=round(budget_spent * 100 / budget_total, 1) if budget_total else None,
        components=components,
        recommendations=sorted(recommendations, key=lambda item: item.priority)[:3],
        limitations=limitations,
    )
