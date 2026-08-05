import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class InboxAddressResponse(BaseModel):
    address: str


class InboundEmailPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    recipient: str = Field(max_length=320)
    sender: str = Field(max_length=320)
    subject: str = Field(default="", max_length=500)
    text: str = Field(default="", max_length=30_000)
    message_id: str | None = Field(default=None, max_length=500)
    received_at: datetime | None = None

    @field_validator("received_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("received_at must include a timezone")
        return value


class SuggestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    transaction_id: uuid.UUID | None
    sender_domain: str
    type: str
    amount_minor: int
    currency: str
    description: str
    occurred_at: datetime
    confidence: float
    status: str
    created_at: datetime
    resolved_at: datetime | None


class SuggestionConfirm(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str | None = Field(default=None, pattern=r"^(income|expense)$")
    amount_minor: int | None = Field(default=None, gt=0)
    category_id: uuid.UUID | None = None
    description: str | None = Field(default=None, max_length=240)
    occurred_at: datetime | None = None

    @field_validator("occurred_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("occurred_at must include a timezone")
        return value
