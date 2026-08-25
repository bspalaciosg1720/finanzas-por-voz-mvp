import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

DEBT_TYPES = (
    "credit_card|consumer_loan|education|vehicle|mortgage|personal_loan|financed_purchase|other"
)


class DebtCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=80)
    debt_type: str = Field(pattern=rf"^({DEBT_TYPES})$")
    initial_balance_minor: int = Field(gt=0, le=9_000_000_000_000_000)
    current_balance_minor: int | None = Field(default=None, gt=0)
    minimum_payment_minor: int = Field(ge=0, le=9_000_000_000_000_000)
    currency: str = Field(default="COP", pattern=r"^[A-Z]{3}$")
    annual_interest_rate_bps: int | None = Field(default=None, ge=0, le=100_000)
    payment_day: int | None = Field(default=None, ge=1, le=31)
    statement_day: int | None = Field(default=None, ge=1, le=31)
    installment_count: int | None = Field(default=None, ge=1, le=1200)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return " ".join(value.split())

    @model_validator(mode="after")
    def validate_balance(self):
        if (
            self.current_balance_minor is not None
            and self.current_balance_minor > self.initial_balance_minor
        ):
            raise ValueError("current balance cannot exceed initial balance")
        return self


class DebtUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=80)
    minimum_payment_minor: int | None = Field(default=None, ge=0)
    annual_interest_rate_bps: int | None = Field(default=None, ge=0, le=100_000)
    payment_day: int | None = Field(default=None, ge=1, le=31)
    statement_day: int | None = Field(default=None, ge=1, le=31)


class DebtPaymentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_minor: int = Field(gt=0, le=9_000_000_000_000_000)
    payment_type: str = Field(default="regular", pattern=r"^(minimum|regular|extra)$")
    paid_at: datetime
    note: str = Field(default="", max_length=120)

    @field_validator("paid_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("paid_at must include a timezone")
        return value


class DebtPaymentUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    amount_minor: int | None = Field(default=None, gt=0, le=9_000_000_000_000_000)
    payment_type: str | None = Field(default=None, pattern=r"^(minimum|regular|extra)$")
    paid_at: datetime | None = None
    note: str | None = Field(default=None, max_length=120)

    @field_validator("paid_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("paid_at must include a timezone")
        return value


class DebtPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    amount_minor: int
    payment_type: str
    paid_at: datetime
    note: str


class DebtResponse(BaseModel):
    id: uuid.UUID
    name: str
    debt_type: str
    initial_balance_minor: int
    current_balance_minor: int
    minimum_payment_minor: int
    currency: str
    annual_interest_rate_bps: int | None
    payment_day: int | None
    statement_day: int | None
    installment_count: int | None
    status: str
    progress_percent: float
    payments: list[DebtPaymentResponse]


class PayoffStep(BaseModel):
    debt_id: uuid.UUID
    name: str
    order: int
    balance_minor: int
    monthly_payment_minor: int
    estimated_months: int | None
    estimated_interest_minor: int | None


class PayoffPlan(BaseModel):
    strategy: str
    currency: str
    minimum_payments_minor: int
    extra_payment_minor: int
    total_monthly_payment_minor: int
    estimated_months: int | None
    estimated_interest_minor: int | None
    steps: list[PayoffStep]
    limitations: list[str]


class PayoffComparison(BaseModel):
    snowball: PayoffPlan
    avalanche: PayoffPlan
    recommended_strategy: str | None
    interest_savings_minor: int | None
