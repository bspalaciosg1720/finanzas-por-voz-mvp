import uuid

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrategyConfigUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    zero_based_enabled: bool | None = None
    pay_first_enabled: bool | None = None
    pay_first_percent: int | None = Field(default=None, ge=1, le=100)
    pay_first_amount_minor: int | None = Field(default=None, gt=0)
    pay_first_goal_id: uuid.UUID | None = None
    variable_income_budget_enabled: bool | None = None
    extraordinary_income_enabled: bool | None = None
    extraordinary_debt_percent: int | None = Field(default=None, ge=0, le=100)
    extraordinary_savings_percent: int | None = Field(default=None, ge=0, le=100)
    extraordinary_goals_percent: int | None = Field(default=None, ge=0, le=100)
    extraordinary_personal_percent: int | None = Field(default=None, ge=0, le=100)
    hybrid_debt_enabled: bool | None = None
    cash_buffer_enabled: bool | None = None
    cash_buffer_target_minor: int | None = Field(default=None, gt=0)
    no_spend_days_enabled: bool | None = None
    no_spend_weekdays: list[int] | None = None
    purchase_wait_enabled: bool | None = None
    purchase_wait_threshold_minor: int | None = Field(default=None, gt=0)
    purchase_wait_hours: int | None = None
    leak_detector_enabled: bool | None = None
    opportunity_cost_enabled: bool | None = None

    @model_validator(mode="after")
    def validate_values(self):
        if self.purchase_wait_hours is not None and self.purchase_wait_hours not in {24, 48}:
            raise ValueError("purchase_wait_hours must be 24 or 48")
        if self.no_spend_weekdays is not None and any(
            day < 0 or day > 6 for day in self.no_spend_weekdays
        ):
            raise ValueError("weekdays must use values from 0 to 6")
        percentages = (
            self.extraordinary_debt_percent,
            self.extraordinary_savings_percent,
            self.extraordinary_goals_percent,
            self.extraordinary_personal_percent,
        )
        if all(value is not None for value in percentages) and sum(percentages) != 100:  # type: ignore[arg-type]
            raise ValueError("extraordinary income percentages must add up to 100")
        return self


class StrategyConfigResponse(BaseModel):
    zero_based_enabled: bool
    pay_first_enabled: bool
    pay_first_percent: int
    pay_first_amount_minor: int | None
    pay_first_goal_id: uuid.UUID | None
    variable_income_budget_enabled: bool
    extraordinary_income_enabled: bool
    extraordinary_debt_percent: int
    extraordinary_savings_percent: int
    extraordinary_goals_percent: int
    extraordinary_personal_percent: int
    hybrid_debt_enabled: bool
    cash_buffer_enabled: bool
    cash_buffer_target_minor: int | None
    no_spend_days_enabled: bool
    no_spend_weekdays: list[int]
    purchase_wait_enabled: bool
    purchase_wait_threshold_minor: int
    purchase_wait_hours: int
    leak_detector_enabled: bool
    opportunity_cost_enabled: bool


class StrategyInsight(BaseModel):
    key: str
    enabled: bool
    recommended: bool
    priority: int
    title: str
    reason: str
    benefit: str
    impact_type: str
    impact_minor: int | None = None
    impact_percent: float | None = None
    limitations: list[str] = Field(default_factory=list)


class StrategyAnalysisResponse(BaseModel):
    period: str
    currency: str
    financial_level: str
    planning_income_minor: int
    received_income_minor: int
    priority_order: list[str]
    strategies: list[StrategyInsight]
