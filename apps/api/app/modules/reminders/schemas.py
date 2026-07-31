from pydantic import BaseModel, ConfigDict, Field


class ReminderPreferencesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    daily_expense_enabled: bool
    weekly_income_enabled: bool
    budget_alerts_enabled: bool
    local_hour: int = Field(ge=0, le=23)
    local_minute: int = Field(ge=0, le=59)


class ReminderPreferencesResponse(ReminderPreferencesUpdate):
    timezone: str


class ReminderCandidate(BaseModel):
    kind: str
    period_key: str
    title: str
    body: str


class ReminderEvaluation(BaseModel):
    candidates: list[ReminderCandidate]
