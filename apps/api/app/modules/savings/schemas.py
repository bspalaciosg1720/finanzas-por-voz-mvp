import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SavingsGoalCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=80)
    target_amount_minor: int = Field(gt=0, le=9_000_000_000_000_000)
    currency: str = Field(default="COP", pattern=r"^[A-Z]{3}$")
    target_date: date | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        return " ".join(value.split())


class SavingsGoalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=80)
    target_amount_minor: int | None = Field(
        default=None,
        gt=0,
        le=9_000_000_000_000_000,
    )
    target_date: date | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if value else value


class SavingsContributionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount_minor: int = Field(gt=0, le=9_000_000_000_000_000)
    contributed_at: datetime
    note: str = Field(default="", max_length=120)

    @field_validator("contributed_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("contributed_at must include a timezone")
        return value


class SavingsContributionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    amount_minor: int
    contributed_at: datetime
    note: str


class SavingsGoalResponse(BaseModel):
    id: uuid.UUID
    name: str
    target_amount_minor: int
    saved_amount_minor: int
    currency: str
    target_date: date | None
    status: str
    progress_percent: float
    contributions: list[SavingsContributionResponse]
