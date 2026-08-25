from pydantic import BaseModel, ConfigDict, Field, model_validator


class SimulationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    scenario: str = Field(
        pattern=r"^(reduce_variable|extra_debt_payment|increase_income|increase_savings|savings_goal)$"
    )
    amount_minor: int = Field(gt=0, le=9_000_000_000_000_000)
    months: int | None = Field(default=None, ge=1, le=600)

    @model_validator(mode="after")
    def require_months_for_goal(self):
        if self.scenario == "savings_goal" and self.months is None:
            raise ValueError("months is required for a savings goal")
        return self


class ScenarioValues(BaseModel):
    available_cash_minor: int
    variable_expense_minor: int
    savings_minor: int
    monthly_goal_amount_minor: int | None = None
    debt_free_months: int | None = None
    debt_interest_minor: int | None = None


class SimulationResponse(BaseModel):
    scenario: str
    currency: str
    current: ScenarioValues
    simulated: ScenarioValues
    limitations: list[str]
    applied: bool = False
