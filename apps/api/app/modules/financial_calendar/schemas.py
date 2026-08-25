import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class ObligationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=80)
    obligation_type: str = Field(
        pattern=r"^(housing|utility|subscription|debt|savings|insurance|family|other)$"
    )
    amount_minor: int = Field(gt=0, le=9_000_000_000_000_000)
    currency: str = Field(default="COP", pattern=r"^[A-Z]{3}$")
    due_day: int = Field(ge=1, le=31)
    category_id: uuid.UUID


class ObligationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    obligation_type: str
    amount_minor: int
    currency: str
    due_day: int
    category_id: uuid.UUID | None


class ObligationUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str | None = Field(default=None, min_length=2, max_length=80)
    amount_minor: int | None = Field(default=None, gt=0, le=9_000_000_000_000_000)
    due_day: int | None = Field(default=None, ge=1, le=31)
    category_id: uuid.UUID | None = None


class ObligationPaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    due_date: date
    paid_at: datetime
    amount_minor: int = Field(gt=0)


class ObligationPaymentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paid_at: datetime | None = None
    amount_minor: int | None = Field(default=None, gt=0)


class CalendarItem(BaseModel):
    obligation_id: uuid.UUID
    name: str
    obligation_type: str
    amount_minor: int
    currency: str
    due_date: date
    days_until_due: int
    status: str
    payment_id: uuid.UUID | None
    category_id: uuid.UUID | None
    category_name: str


class FinancialCalendarResponse(BaseModel):
    items: list[CalendarItem]
    concentrated_weeks: list[str]
