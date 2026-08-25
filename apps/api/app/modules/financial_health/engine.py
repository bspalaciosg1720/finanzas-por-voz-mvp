from dataclasses import dataclass

from app.modules.financial_health.schemas import HealthComponent


@dataclass(frozen=True)
class HealthInputs:
    income_minor: int
    essential_expense_minor: int
    variable_expense_minor: int
    unclassified_expense_minor: int
    savings_minor: int
    budget_total_minor: int
    budget_spent_minor: int
    total_debt_minor: int
    minimum_debt_payments_minor: int
    emergency_fund_minor: int
    obligations_due: int
    obligations_paid: int


def _ratio(value: int, income: int) -> float | None:
    return round((value / income) * 100, 1) if income > 0 else None


def calculate_components(values: HealthInputs) -> list[HealthComponent]:
    if values.income_minor <= 0:
        return []

    expenses = (
        values.essential_expense_minor
        + values.variable_expense_minor
        + values.unclassified_expense_minor
    )
    available = values.income_minor - expenses
    cash_ratio = available / values.income_minor
    cash_score = (
        30 if cash_ratio >= 0.2 else 24 if cash_ratio >= 0.1 else 17 if cash_ratio >= 0 else 4
    )

    essential_ratio = values.essential_expense_minor / values.income_minor
    needs_score = (
        20
        if essential_ratio <= 0.5
        else 16
        if essential_ratio <= 0.6
        else 10
        if essential_ratio <= 0.75
        else 4
    )

    savings_ratio = values.savings_minor / values.income_minor
    savings_score = (
        15
        if savings_ratio >= 0.2
        else 11
        if savings_ratio >= 0.1
        else 6
        if savings_ratio > 0
        else 0
    )

    components = [
        HealthComponent(
            key="cash_flow",
            label="Flujo de caja",
            score=cash_score,
            maximum=30,
            explanation="Tus ingresos cubren tus gastos del mes."
            if available >= 0
            else "Tus gastos superan tus ingresos del mes.",
        ),
        HealthComponent(
            key="essential_expenses",
            label="Gastos esenciales",
            score=needs_score,
            maximum=20,
            explanation=(
                f"Representan "
                f"{_ratio(values.essential_expense_minor, values.income_minor)} % "
                "de tus ingresos."
            ),
        ),
        HealthComponent(
            key="savings",
            label="Ahorro registrado",
            score=savings_score,
            maximum=15,
            explanation=(
                f"Registraste {_ratio(values.savings_minor, values.income_minor)} % "
                "de tus ingresos como aportes a metas."
            ),
        ),
    ]
    if values.budget_total_minor > 0:
        used = values.budget_spent_minor / values.budget_total_minor
        budget_score = 10 if used <= 0.85 else 7 if used <= 1 else 3
        components.append(
            HealthComponent(
                key="budgets",
                label="Presupuestos",
                score=budget_score,
                maximum=10,
                explanation=f"Has utilizado {round(used * 100, 1)} % de tus presupuestos activos.",
            )
        )
    if values.total_debt_minor > 0:
        burden = values.minimum_debt_payments_minor / values.income_minor
        debt_score = 25 if burden <= 0.15 else 18 if burden <= 0.3 else 10 if burden <= 0.4 else 3
        components.append(
            HealthComponent(
                key="debt",
                label="Endeudamiento",
                score=debt_score,
                maximum=25,
                explanation=(
                    f"Tus pagos mínimos representan {round(burden * 100, 1)} % de tus ingresos."
                ),
            )
        )
    coverage = (
        values.emergency_fund_minor / values.essential_expense_minor
        if values.essential_expense_minor > 0
        else None
    )
    if coverage is not None:
        emergency_score = (
            15
            if coverage >= 3
            else 12
            if coverage >= 2
            else 8
            if coverage >= 1
            else 4
            if coverage > 0
            else 0
        )
        components.append(
            HealthComponent(
                key="emergency_fund",
                label="Fondo de emergencia",
                score=emergency_score,
                maximum=15,
                explanation=f"Tu fondo cubre {round(coverage, 2)} meses de gastos esenciales.",
            )
        )
    if values.obligations_due > 0:
        compliance = values.obligations_paid / values.obligations_due
        payment_score = 5 if compliance >= 1 else 3 if compliance >= 0.8 else 1
        components.append(
            HealthComponent(
                key="payments",
                label="Pagos registrados",
                score=payment_score,
                maximum=5,
                explanation=(
                    f"Registraste {values.obligations_paid} de "
                    f"{values.obligations_due} obligaciones del periodo."
                ),
            )
        )
    return components


def normalized_score(components: list[HealthComponent]) -> int | None:
    maximum = sum(item.maximum for item in components)
    return round(sum(item.score for item in components) * 100 / maximum) if maximum else None


def score_status(score: int | None) -> str:
    if score is None:
        return "Necesitamos más datos"
    if score >= 80:
        return "Estable"
    if score >= 60:
        return "En progreso"
    if score >= 40:
        return "Requiere atención"
    return "Prioridad alta"
