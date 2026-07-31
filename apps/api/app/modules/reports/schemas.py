from datetime import date
from typing import Literal

from pydantic import BaseModel

ReportPeriod = Literal["daily", "weekly", "monthly", "annual"]


class ReportCategory(BaseModel):
    category_id: str | None
    name: str
    amount_minor: int
    percentage: float


class ReportPoint(BaseModel):
    label: str
    income_minor: int
    expense_minor: int


class ReportSummary(BaseModel):
    period: ReportPeriod
    start_date: date
    end_date: date
    currency: str
    income_minor: int
    expense_minor: int
    balance_minor: int
    transaction_count: int
    previous_income_minor: int
    previous_expense_minor: int
    expense_change_percent: float | None
    categories: list[ReportCategory]
    series: list[ReportPoint]
