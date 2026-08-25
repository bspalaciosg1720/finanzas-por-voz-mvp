from pydantic import BaseModel, ConfigDict, Field


class FinancialAlert(BaseModel):
    key: str
    kind: str
    priority: int
    tone: str
    title: str
    detail: str
    action_path: str | None = None


class FinancialAlertsResponse(BaseModel):
    items: list[FinancialAlert]
    total_candidates: int


class FinancialAlertDismiss(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str = Field(min_length=3, max_length=160, pattern=r"^[a-z0-9:_-]+$")
