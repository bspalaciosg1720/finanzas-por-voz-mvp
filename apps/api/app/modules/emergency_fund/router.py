import uuid
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.dashboard.service import _month_bounds
from app.modules.emergency_fund.schemas import (
    EmergencyFundConfigure,
    EmergencyFundEventCreate,
    EmergencyFundEventResponse,
    EmergencyFundEventUpdate,
    EmergencyFundResponse,
)
from app.modules.emergency_fund.service import (
    add_event,
    delete_event,
    fund_response,
    get_or_create_fund,
    update_event,
)

router = APIRouter(prefix="/emergency-fund", tags=["Emergency fund"])
DbSession = Annotated[Session, Depends(get_db)]
IdempotencyKey = Annotated[uuid.UUID, Header(alias="Idempotency-Key")]


def bounds(user: CurrentUser):
    now = datetime.now(ZoneInfo(user.timezone))
    return _month_bounds(now.year, now.month, user.timezone)


@router.get("", response_model=EmergencyFundResponse)
def get_fund(user: CurrentUser, db: DbSession):
    return fund_response(db, user, *bounds(user))


@router.patch("", status_code=status.HTTP_204_NO_CONTENT)
def configure_fund(payload: EmergencyFundConfigure, user: CurrentUser, db: DbSession):
    fund = get_or_create_fund(db, user)
    fund.target_months = payload.target_months
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/events", response_model=EmergencyFundEventResponse, status_code=status.HTTP_201_CREATED
)
def create_event(
    payload: EmergencyFundEventCreate,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: IdempotencyKey,
):
    return add_event(db, user, payload, idempotency_key)


@router.patch("/events/{event_id}", response_model=EmergencyFundEventResponse)
def edit_event(
    event_id: uuid.UUID,
    payload: EmergencyFundEventUpdate,
    user: CurrentUser,
    db: DbSession,
):
    return update_event(db, user, event_id, payload)


@router.delete("/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_event(event_id: uuid.UUID, user: CurrentUser, db: DbSession):
    delete_event(db, user, event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
