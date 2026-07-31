import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BudgetCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category_id: uuid.UUID
    amount_minor: int = Field(gt=0, le=9_000_000_000_000_000)
    currency: str = Field(default="COP", pattern=r"^[A-Z]{3}$")
    alert_threshold_percent: int = Field(default=80, ge=1, le=100)


class BudgetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_minor: int | None = Field(default=None, gt=0, le=9_000_000_000_000_000)
    alert_threshold_percent: int | None = Field(default=None, ge=1, le=100)


class BudgetResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    category_name: str
    amount_minor: int
    spent_minor: int
    currency: str
    alert_threshold_percent: int
    progress_percent: float
    alert_status: str


class BudgetAlertResponse(BaseModel):
    id: uuid.UUID
    budget_id: uuid.UUID
    period_start: date
    level: str
    category_name: str
    read_at: datetime | None
    created_at: datetime
