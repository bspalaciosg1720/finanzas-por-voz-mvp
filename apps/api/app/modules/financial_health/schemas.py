from pydantic import BaseModel


class HealthComponent(BaseModel):
    key: str
    label: str
    score: int
    maximum: int
    explanation: str


class HealthRecommendation(BaseModel):
    priority: int
    title: str
    detail: str


class FinancialHealthSummary(BaseModel):
    period: str
    currency: str
    score: int | None
    status: str
    confidence: str
    income_minor: int
    essential_expense_minor: int
    variable_expense_minor: int
    unclassified_expense_minor: int
    total_expense_minor: int
    available_cash_minor: int
    savings_minor: int
    total_debt_minor: int
    minimum_debt_payments_minor: int
    debt_payments_minor: int
    emergency_fund_minor: int
    emergency_fund_months: float | None
    pending_replenishment_minor: int
    essential_percent: float | None
    variable_percent: float | None
    savings_percent: float | None
    debt_payment_percent: float | None
    budget_used_percent: float | None
    components: list[HealthComponent]
    recommendations: list[HealthRecommendation]
    limitations: list[str]


class HealthHistoryItem(BaseModel):
    period: str
    score: int
    status: str
    formula_version: str
    change: int | None


class HealthHistoryResponse(BaseModel):
    items: list[HealthHistoryItem]
    trend: str


class FinancialPattern(BaseModel):
    key: str
    direction: str
    title: str
    detail: str
    start_period: str
    end_period: str
    previous_amount_minor: int | None = None
    current_amount_minor: int | None = None
    change_percent: float | None = None
    category_name: str | None = None


class FinancialPatternsResponse(BaseModel):
    currency: str
    months_analyzed: int
    periods: list[str]
    patterns: list[FinancialPattern]
    limitations: list[str]


class MonthlyIncome(BaseModel):
    period: str
    amount_minor: int


class IncomeProfileResponse(BaseModel):
    currency: str
    classification: str
    months_analyzed: int
    months_with_income: int
    average_income_minor: int | None
    median_income_minor: int | None
    conservative_income_minor: int | None
    variability_percent: float | None
    monthly_incomes: list[MonthlyIncome]
    explanation: str
    limitations: list[str]


class ExtraIncomeAllocation(BaseModel):
    destination: str
    label: str
    amount_minor: int
    rationale: str


class ExtraIncomeAnalysisResponse(BaseModel):
    period: str
    currency: str
    detected: bool
    source: str
    current_income_minor: int
    conservative_income_minor: int | None
    extra_income_minor: int
    applied: bool
    explanation: str
    allocations: list[ExtraIncomeAllocation]
    limitations: list[str]
