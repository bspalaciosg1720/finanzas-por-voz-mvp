from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.dashboard.service import _month_bounds
from app.modules.financial_health.extra_income import analyze_extra_income
from app.modules.financial_health.history import get_history, save_snapshot
from app.modules.financial_health.income import get_income_profile
from app.modules.financial_health.patterns import detect_patterns
from app.modules.financial_health.schemas import (
    ExtraIncomeAnalysisResponse,
    FinancialHealthSummary,
    FinancialPatternsResponse,
    HealthHistoryResponse,
    IncomeProfileResponse,
)
from app.modules.financial_health.service import get_financial_health

router = APIRouter(prefix="/financial-health", tags=["Financial health"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/summary", response_model=FinancialHealthSummary)
def financial_health_summary(
    user: CurrentUser,
    db: DbSession,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> FinancialHealthSummary:
    local_now = datetime.now(ZoneInfo(user.timezone))
    selected_year, selected_month = year or local_now.year, month or local_now.month
    start, end = _month_bounds(selected_year, selected_month, user.timezone)
    summary = get_financial_health(db, user, start=start, end=end)
    save_snapshot(db, user, summary)
    return summary


@router.get("/history", response_model=HealthHistoryResponse)
def financial_health_history(
    user: CurrentUser,
    db: DbSession,
    months: Annotated[int, Query(ge=1, le=12)] = 6,
) -> HealthHistoryResponse:
    return get_history(db, user, months)


@router.get("/patterns", response_model=FinancialPatternsResponse)
def financial_patterns(
    user: CurrentUser,
    db: DbSession,
    months: Annotated[int, Query(ge=3, le=6)] = 3,
) -> FinancialPatternsResponse:
    return detect_patterns(db, user, months=months)


@router.get("/income-profile", response_model=IncomeProfileResponse)
def income_profile(
    user: CurrentUser,
    db: DbSession,
    months: Annotated[int, Query(ge=3, le=12)] = 6,
) -> IncomeProfileResponse:
    return get_income_profile(db, user, months=months)


@router.get("/extra-income", response_model=ExtraIncomeAnalysisResponse)
def extra_income_analysis(
    user: CurrentUser,
    db: DbSession,
    amount_minor: Annotated[int | None, Query(gt=0, le=9_000_000_000_000_000)] = None,
) -> ExtraIncomeAnalysisResponse:
    return analyze_extra_income(db, user, supplied_amount_minor=amount_minor)
