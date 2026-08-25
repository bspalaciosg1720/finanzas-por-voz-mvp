from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.budgets.service import list_budget_progress
from app.modules.categories.models import Category
from app.modules.dashboard.service import _month_bounds
from app.modules.debts.models import Debt
from app.modules.debts.service import payoff_plan
from app.modules.financial_health.classification import ESSENTIAL_SLUGS
from app.modules.financial_health.extra_income import analyze_extra_income
from app.modules.financial_health.income import get_income_profile
from app.modules.financial_health.service import get_financial_health
from app.modules.financial_strategies.models import FinancialStrategyConfig
from app.modules.financial_strategies.schemas import (
    StrategyAnalysisResponse,
    StrategyConfigResponse,
    StrategyConfigUpdate,
    StrategyInsight,
)
from app.modules.savings.models import SavingsGoal
from app.modules.transactions.accounting import CONSUMPTION_ROLES
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


def get_or_create_config(db: Session, user: User) -> FinancialStrategyConfig:
    config = db.get(FinancialStrategyConfig, user.id)
    if config is None:
        config = FinancialStrategyConfig(user_id=user.id)
        db.add(config)
        db.commit()
        db.refresh(config)
    return config


def config_response(config: FinancialStrategyConfig) -> StrategyConfigResponse:
    values = {
        column.name: getattr(config, column.name)
        for column in FinancialStrategyConfig.__table__.columns
        if column.name not in {"user_id", "updated_at"}
    }
    values["no_spend_weekdays"] = [
        int(value) for value in config.no_spend_weekdays.split(",") if value
    ]
    return StrategyConfigResponse(**values)


def update_config(db: Session, user: User, payload: StrategyConfigUpdate) -> StrategyConfigResponse:
    config = get_or_create_config(db, user)
    values = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "pay_first_goal_id" in values:
        goal = db.scalar(
            select(SavingsGoal).where(
                SavingsGoal.id == values["pay_first_goal_id"],
                SavingsGoal.user_id == user.id,
                SavingsGoal.status == "active",
            )
        )
        if goal is None:
            from app.core.errors import AppError

            raise AppError(
                status=422,
                title="Invalid pay-first goal",
                detail="Choose an active savings goal owned by this account.",
                error_type="invalid-pay-first-goal",
            )
    if "no_spend_weekdays" in values:
        values["no_spend_weekdays"] = ",".join(
            str(day) for day in sorted(set(values["no_spend_weekdays"]))
        )
    percentage_fields = (
        "extraordinary_debt_percent",
        "extraordinary_savings_percent",
        "extraordinary_goals_percent",
        "extraordinary_personal_percent",
    )
    proposed = {field: values.get(field, getattr(config, field)) for field in percentage_fields}
    if sum(proposed.values()) != 100:
        from app.core.errors import AppError

        raise AppError(
            status=422,
            title="Invalid extraordinary income allocation",
            detail="The four extraordinary income percentages must add up to 100.",
            error_type="invalid-extraordinary-allocation",
        )
    for field, value in values.items():
        setattr(config, field, value)
    db.commit()
    db.refresh(config)
    return config_response(config)


def _insight(
    key: str,
    enabled: bool,
    recommended: bool,
    priority: int,
    title: str,
    reason: str,
    benefit: str,
    impact_type: str,
    impact_minor: int | None = None,
    impact_percent: float | None = None,
    limitations: list[str] | None = None,
) -> StrategyInsight:
    return StrategyInsight(
        key=key,
        enabled=enabled,
        recommended=recommended,
        priority=priority,
        title=title,
        reason=reason,
        benefit=benefit,
        impact_type=impact_type,
        impact_minor=impact_minor,
        impact_percent=impact_percent,
        limitations=limitations or [],
    )


def analyze_strategies(db: Session, user: User) -> StrategyAnalysisResponse:
    config = get_or_create_config(db, user)
    local_now = datetime.now(ZoneInfo(user.timezone))
    start, end = _month_bounds(local_now.year, local_now.month, user.timezone)
    health = get_financial_health(db, user, start=start, end=end)
    profile = get_income_profile(db, user, months=6)
    planning_income = profile.conservative_income_minor or health.income_minor
    budgets = list_budget_progress(db, user)
    budget_total = sum(item.amount_minor for item in budgets)
    active_goals = list(
        db.scalars(
            select(SavingsGoal).where(
                SavingsGoal.user_id == user.id, SavingsGoal.status == "active"
            )
        )
    )
    planned_savings = sum(item.planned_monthly_minor or 0 for item in active_goals)
    assigned = budget_total + planned_savings + health.minimum_debt_payments_minor
    unassigned = planning_income - assigned
    insights: list[StrategyInsight] = []

    insights.append(
        _insight(
            "zero_based",
            config.zero_based_enabled,
            planning_income > 0 and unassigned != 0,
            5,
            "Presupuesto base cero",
            f"Hay {abs(unassigned)} sin asignar."
            if unassigned >= 0
            else f"Las asignaciones exceden el ingreso base por {abs(unassigned)}.",
            "Da un destino explícito al ingreso sin obligar a gastarlo.",
            "unassigned_cash",
            unassigned,
        )
    )
    safe_savings = max(
        0,
        planning_income - health.essential_expense_minor - health.minimum_debt_payments_minor,
    )
    pay_first_target = config.pay_first_amount_minor or round(
        planning_income * config.pay_first_percent / 100
    )
    pay_first = min(safe_savings, pay_first_target)
    insights.append(
        _insight(
            "pay_first",
            config.pay_first_enabled,
            planning_income > 0 and pay_first > 0 and health.savings_minor < pay_first,
            6,
            "Págate primero",
            f"La capacidad segura estimada es {safe_savings}; "
            f"la meta configurada es {pay_first_target}.",
            "Separaría ahorro solo después de proteger necesidades y mínimos de deuda.",
            "monthly_savings",
            pay_first,
            round(pay_first * 100 / planning_income, 1) if planning_income else None,
            ["La transferencia requiere confirmación; el análisis no mueve dinero."],
        )
    )
    envelope_available = sum(max(0, item.amount_minor - item.spent_minor) for item in budgets)
    insights.append(
        _insight(
            "digital_envelopes",
            bool(budgets),
            not budgets or any(item.alert_status != "on_track" for item in budgets),
            4,
            "Sobres digitales",
            f"Hay {len(budgets)} sobres con {envelope_available} disponibles.",
            "Permite controlar consumo y recibir alertas antes del límite.",
            "envelope_available",
            envelope_available,
        )
    )
    insights.append(
        _insight(
            "variable_income_budget",
            config.variable_income_budget_enabled,
            profile.classification == "variable",
            2,
            "Presupuesto para ingresos variables",
            profile.explanation,
            "Evita comprometer ingresos que todavía no se han recibido.",
            "planning_income",
            planning_income,
            profile.variability_percent,
            profile.limitations,
        )
    )
    extra = analyze_extra_income(db, user)
    allocation_text = (
        f"Deuda {config.extraordinary_debt_percent} %, ahorro "
        f"{config.extraordinary_savings_percent} %, metas "
        f"{config.extraordinary_goals_percent} % y personal "
        f"{config.extraordinary_personal_percent} %."
    )
    insights.append(
        _insight(
            "extraordinary_income",
            config.extraordinary_income_enabled,
            extra.detected,
            5,
            "Regla para ingresos extraordinarios",
            allocation_text,
            "Distribuye excedentes con porcentajes configurables sin aplicarlos automáticamente.",
            "extra_income",
            extra.extra_income_minor,
            limitations=extra.limitations,
        )
    )
    active_debts = list(
        db.scalars(select(Debt).where(Debt.user_id == user.id, Debt.status == "active"))
    )
    hybrid_impact = None
    hybrid_limitations = []
    if len(active_debts) >= 2:
        hybrid = payoff_plan(db, user, strategy="hybrid", extra_payment_minor=0)
        avalanche = payoff_plan(db, user, strategy="avalanche", extra_payment_minor=0)
        if (
            hybrid.estimated_interest_minor is not None
            and avalanche.estimated_interest_minor is not None
        ):
            hybrid_impact = hybrid.estimated_interest_minor - avalanche.estimated_interest_minor
        hybrid_limitations = hybrid.limitations
    insights.append(
        _insight(
            "hybrid_debt",
            config.hybrid_debt_enabled,
            len(active_debts) >= 2,
            4,
            "Estrategia híbrida de deuda",
            "Elimina primero la deuda de menor saldo y después prioriza la tasa más alta.",
            "Combina una victoria temprana con reducción posterior de intereses.",
            "interest_difference_vs_avalanche",
            hybrid_impact,
            limitations=hybrid_limitations,
        )
    )
    sinking = [item for item in active_goals if item.goal_type == "sinking_fund"]
    insights.append(
        _insight(
            "sinking_funds",
            bool(sinking),
            not sinking,
            7,
            "Fondos para gastos futuros",
            f"Hay {len(sinking)} fondos y "
            f"{sum(item.planned_monthly_minor or 0 for item in sinking)} planeados al mes.",
            "Convierte gastos previsibles en aportes mensuales manejables.",
            "monthly_contribution",
            sum(item.planned_monthly_minor or 0 for item in sinking),
        )
    )
    buffer_target = config.cash_buffer_target_minor or max(100_000, round(planning_income * 0.1))
    buffer_gap = max(0, buffer_target - max(0, health.available_cash_minor))
    insights.append(
        _insight(
            "cash_buffer",
            config.cash_buffer_enabled,
            planning_income > 0 and buffer_gap > 0,
            3,
            "Colchón de flujo de caja",
            f"El objetivo es {buffer_target} y faltan {buffer_gap} "
            "según el flujo disponible actual.",
            "Reduce el riesgo de quedarse sin liquidez antes del próximo ingreso.",
            "buffer_gap",
            buffer_gap,
        )
    )

    transaction_rows = db.execute(
        select(Transaction, Category.slug)
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
    ).all()
    variable_transactions = [
        item for item, slug in transaction_rows if slug is not None and slug not in ESSENTIAL_SLUGS
    ]
    weekdays = {int(value) for value in config.no_spend_weekdays.split(",") if value}
    elapsed_dates = {
        item.occurred_at.astimezone(ZoneInfo(user.timezone)).date()
        for item in variable_transactions
    }
    scheduled_days = sum(
        1
        for day in range(1, local_now.day + 1)
        if datetime(local_now.year, local_now.month, day).weekday() in weekdays
    )
    spent_scheduled_days = sum(1 for day in elapsed_dates if day.weekday() in weekdays)
    successful_days = max(0, scheduled_days - spent_scheduled_days)
    average_daily_variable = round(health.variable_expense_minor / max(1, local_now.day))
    no_spend_impact = successful_days * average_daily_variable
    insights.append(
        _insight(
            "no_spend_days",
            config.no_spend_days_enabled,
            bool(weekdays and health.variable_expense_minor),
            8,
            "Días sin gasto",
            f"Se cumplieron {successful_days} de {scheduled_days} días programados este mes.",
            "Muestra el impacto conseguido sin restringir necesidades básicas.",
            "avoidable_spend",
            no_spend_impact,
        )
    )
    wait_candidates = [
        item
        for item in variable_transactions
        if item.amount_minor >= config.purchase_wait_threshold_minor
    ]
    wait_total = sum(item.amount_minor for item in wait_candidates)
    insights.append(
        _insight(
            "purchase_wait",
            config.purchase_wait_enabled,
            bool(wait_candidates),
            7,
            "Regla de espera para compras",
            f"Hay {len(wait_candidates)} compras sobre el umbral de "
            f"{config.purchase_wait_threshold_minor}.",
            f"Sugiere esperar {config.purchase_wait_hours} horas sin bloquear la decisión.",
            "purchases_to_review",
            wait_total,
        )
    )
    small_limit = max(10_000, round(planning_income * 0.02))
    grouped: dict[object, list[int]] = defaultdict(list)
    for item in variable_transactions:
        if item.amount_minor <= small_limit:
            grouped[item.category_id].append(item.amount_minor)
    leaks = [values for values in grouped.values() if len(values) >= 4]
    leak_total = max((sum(values) for values in leaks), default=0)
    leak_count = max((len(values) for values in leaks), default=0)
    insights.append(
        _insight(
            "financial_leaks",
            config.leak_detector_enabled,
            leak_total > 0,
            6,
            "Detector de fugas financieras",
            f"La agrupación más frecuente suma {leak_total} en {leak_count} gastos pequeños.",
            "Hace visible el acumulado mensual sin juzgar cada compra.",
            "monthly_leak",
            leak_total,
        )
    )
    largest_purchase = max((item.amount_minor for item in wait_candidates), default=0)
    target_goal = active_goals[0] if active_goals else None
    opportunity = (
        round(largest_purchase * 100 / target_goal.target_amount_minor, 1)
        if target_goal and target_goal.target_amount_minor
        else None
    )
    insights.append(
        _insight(
            "opportunity_cost",
            config.opportunity_cost_enabled,
            bool(largest_purchase and target_goal),
            8,
            "Costo de oportunidad",
            (
                f"La compra mayor podría avanzar {opportunity} % la meta {target_goal.name}."
                if target_goal and opportunity is not None
                else "Se necesita una compra relevante y una meta activa para comparar."
            ),
            "Compara alternativas sin impedir ni calificar la decisión.",
            "purchase_value",
            largest_purchase or None,
            opportunity,
        )
    )

    if health.available_cash_minor < 0:
        level = "stabilize"
    elif health.emergency_fund_months is None or health.emergency_fund_months < 1:
        level = "protect"
    elif health.total_debt_minor > 0:
        level = "debt_freedom"
    elif health.emergency_fund_months < 3:
        level = "build"
    else:
        level = "grow"
    priorities = [
        "basic_needs",
        "upcoming_payments",
        "minimum_debt_payments",
        "emergency_fund",
        "priority_debt",
        "savings",
        "goals",
        "discretionary_spending",
    ]
    insights.extend(
        [
            _insight(
                "automatic_priorities",
                True,
                True,
                1,
                "Orden automático de prioridades",
                "Las recomendaciones respetan necesidades, vencimientos y mínimos "
                "antes de optimizar.",
                "Evita sugerir ahorro o abonos que comprometan obligaciones básicas.",
                "priority_sequence",
            ),
            _insight(
                "financial_level",
                True,
                True,
                2,
                "Nivel financiero adaptativo",
                f"La etapa actual es {level} según flujo, reserva y deuda.",
                "Adapta los consejos a la necesidad financiera más inmediata.",
                "financial_stage",
            ),
        ]
    )
    return StrategyAnalysisResponse(
        period=health.period,
        currency=user.default_currency,
        financial_level=level,
        planning_income_minor=planning_income,
        received_income_minor=health.income_minor,
        priority_order=priorities,
        strategies=sorted(insights, key=lambda item: (item.priority, item.key)),
    )
