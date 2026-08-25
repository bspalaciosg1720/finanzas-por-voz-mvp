import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EmergencyFundConfigure(BaseModel):
    model_config = ConfigDict(extra="forbid")
    target_months: int = Field(ge=1, le=24)


class EmergencyFundEventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: str = Field(pattern=r"^(deposit|withdrawal)$")
    amount_minor: int = Field(gt=0, le=9_000_000_000_000_000)
    occurred_at: datetime
    note: str = Field(default="", max_length=120)

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class EmergencyFundEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: str
    amount_minor: int
    occurred_at: datetime
    note: str


class EmergencyFundEventUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_type: str | None = Field(default=None, pattern=r"^(deposit|withdrawal)$")
    amount_minor: int | None = Field(default=None, gt=0, le=9_000_000_000_000_000)
    occurred_at: datetime | None = None
    note: str | None = Field(default=None, max_length=120)

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("occurred_at must include a timezone")
        return value


class EmergencyFundResponse(BaseModel):
    currency: str
    target_months: int
    balance_minor: int
    pending_replenishment_minor: int
    essential_expense_minor: int
    target_amount_minor: int
    coverage_months: float | None
    progress_percent: float | None
    events: list[EmergencyFundEventResponse]
