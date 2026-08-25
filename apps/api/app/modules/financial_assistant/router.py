from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.dashboard.service import _month_bounds
from app.modules.financial_assistant.schemas import AssistantAnswer, AssistantQuestion
from app.modules.financial_assistant.service import explain_with_ai
from app.modules.financial_health.service import get_financial_health

router = APIRouter(prefix="/financial-assistant", tags=["Financial assistant"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/explain", response_model=AssistantAnswer)
def explain(payload: AssistantQuestion, user: CurrentUser, db: DbSession):
    now = datetime.now(ZoneInfo(user.timezone))
    start, end = _month_bounds(now.year, now.month, user.timezone)
    summary = get_financial_health(db, user, start=start, end=end)
    return explain_with_ai(get_settings(), summary, payload.question)
