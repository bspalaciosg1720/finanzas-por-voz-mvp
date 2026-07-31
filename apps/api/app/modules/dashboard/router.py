from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.dashboard.schemas import DashboardSummary
from app.modules.dashboard.service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    user: CurrentUser,
    db: DbSession,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
    month: Annotated[int | None, Query(ge=1, le=12)] = None,
) -> DashboardSummary:
    local_now = datetime.now(ZoneInfo(user.timezone))
    selected_year = year or local_now.year
    selected_month = month or local_now.month
    return get_dashboard_summary(
        db,
        user,
        year=selected_year,
        month=selected_month,
    )
