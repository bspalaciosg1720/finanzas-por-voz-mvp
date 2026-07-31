from pydantic import BaseModel

from app.modules.transactions.schemas import TransactionResponse


class TopExpenseCategory(BaseModel):
    category_id: str | None
    name: str
    amount_minor: int


class DashboardSummary(BaseModel):
    currency: str
    period: str
    balance_minor: int
    income_minor: int
    expense_minor: int
    previous_income_minor: int
    previous_expense_minor: int
    expense_change_percent: float | None
    top_expense_category: TopExpenseCategory | None
    recent_transactions: list[TransactionResponse]
