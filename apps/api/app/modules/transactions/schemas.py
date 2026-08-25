import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(pattern=r"^(income|expense)$")
    amount_minor: int = Field(gt=0, le=9_000_000_000_000_000)
    currency: str = Field(default="COP", pattern=r"^[A-Z]{3}$")
    category_id: uuid.UUID | None = None
    description: str = Field(default="", max_length=240)
    occurred_at: datetime
    source: str = Field(default="manual", pattern=r"^(manual|voice|import|integration)$")

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return " ".join(value.split())


class TransactionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str | None = Field(default=None, pattern=r"^(income|expense)$")
    amount_minor: int | None = Field(default=None, gt=0, le=9_000_000_000_000_000)
    category_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=240)
    occurred_at: datetime | None = None

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("occurred_at must include a timezone")
        return value

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str | None) -> str | None:
        return " ".join(value.split()) if value is not None else None


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category_id: uuid.UUID | None
    type: str
    amount_minor: int
    currency: str
    description: str
    occurred_at: datetime
    source: str
    financial_role: str
    status: str
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TransactionPage(BaseModel):
    items: list[TransactionResponse]
    next_cursor: str | None
