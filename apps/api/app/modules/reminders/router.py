from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.reminders.schemas import (
    ReminderEvaluation,
    ReminderPreferencesResponse,
    ReminderPreferencesUpdate,
)
from app.modules.reminders.service import (
    evaluate_reminders,
    get_or_create_preferences,
    public_preferences,
    update_preferences,
)

router = APIRouter(prefix="/reminders", tags=["Reminders"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/preferences", response_model=ReminderPreferencesResponse)
def get_preferences(
    user: CurrentUser, db: DbSession
) -> ReminderPreferencesResponse:
    return public_preferences(get_or_create_preferences(db, user), user)


@router.put("/preferences", response_model=ReminderPreferencesResponse)
def put_preferences(
    payload: ReminderPreferencesUpdate,
    user: CurrentUser,
    db: DbSession,
) -> ReminderPreferencesResponse:
    return update_preferences(db, user, payload)


@router.post("/evaluate", response_model=ReminderEvaluation)
def evaluate(user: CurrentUser, db: DbSession) -> ReminderEvaluation:
    return evaluate_reminders(db, user, now=datetime.now(UTC))
