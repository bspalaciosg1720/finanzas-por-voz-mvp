import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class VoiceInterpretationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transcript: str = Field(min_length=1, max_length=500)
    reference_at: datetime | None = None

    @field_validator("transcript")
    @classmethod
    def normalize_transcript(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("transcript cannot be blank")
        return normalized

    @field_validator("reference_at")
    @classmethod
    def require_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("reference_at must include a timezone")
        return value


class FieldConfidence(BaseModel):
    amount: float = Field(ge=0, le=1)
    movement_type: float = Field(ge=0, le=1)
    category: float = Field(ge=0, le=1)
    description: float = Field(ge=0, le=1)
    occurred_at: float = Field(ge=0, le=1)


class VoiceInterpretationResponse(BaseModel):
    interaction_id: uuid.UUID
    transcript: str
    movement_type: str | None
    amount_minor: int | None
    currency: str
    category_id: uuid.UUID | None
    category_name: str | None
    description: str
    occurred_at: datetime
    confidence: FieldConfidence
    ambiguities: list[str]
    requires_confirmation: bool


class AudioTranscriptionResponse(BaseModel):
    transcript: str
    provider: str


class VoiceInteractionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    outcome: str = Field(pattern=r"^(completed|abandoned)$")
    corrected_fields: list[str] = Field(default_factory=list, max_length=5)
    duration_ms: int | None = Field(default=None, ge=0, le=300_000)

    @field_validator("corrected_fields")
    @classmethod
    def validate_corrected_fields(cls, value: list[str]) -> list[str]:
        allowed = {"amount", "movement_type", "category", "description", "occurred_at"}
        unique = sorted(set(value))
        if any(field not in allowed for field in unique):
            raise ValueError("corrected_fields contains an unsupported field")
        return unique
