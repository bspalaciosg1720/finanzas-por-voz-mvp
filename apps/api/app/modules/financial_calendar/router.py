import uuid
from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.financial_calendar.schemas import (
    FinancialCalendarResponse,
    ObligationCreate,
    ObligationPaymentCreate,
    ObligationPaymentUpdate,
    ObligationResponse,
    ObligationUpdate,
)
from app.modules.financial_calendar.service import (
    add_payment,
    archive_obligation,
    calendar_view,
    create_obligation,
    delete_payment,
    list_obligations,
    update_obligation,
    update_payment,
)

router = APIRouter(prefix="/financial-calendar", tags=["Financial calendar"])
DbSession = Annotated[Session, Depends(get_db)]
IdempotencyKey = Annotated[uuid.UUID, Header(alias="Idempotency-Key")]


@router.get("/obligations", response_model=list[ObligationResponse])
def obligations(user: CurrentUser, db: DbSession):
    return list_obligations(db, user)


@router.post("/obligations", response_model=ObligationResponse, status_code=status.HTTP_201_CREATED)
def create(payload: ObligationCreate, user: CurrentUser, db: DbSession):
    return create_obligation(db, user, payload)


@router.patch("/obligations/{obligation_id}", response_model=ObligationResponse)
def edit_obligation(
    obligation_id: uuid.UUID,
    payload: ObligationUpdate,
    user: CurrentUser,
    db: DbSession,
):
    return update_obligation(db, user, obligation_id, payload)


@router.delete("/obligations/{obligation_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_obligation(obligation_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    archive_obligation(db, user, obligation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/obligations/{obligation_id}/payments", status_code=status.HTTP_201_CREATED)
def pay(
    obligation_id: uuid.UUID,
    payload: ObligationPaymentCreate,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: IdempotencyKey,
):
    payment = add_payment(db, user, obligation_id, payload, idempotency_key)
    return {"id": str(payment.id)}


@router.patch("/obligations/{obligation_id}/payments/{payment_id}")
def edit_payment(
    obligation_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: ObligationPaymentUpdate,
    user: CurrentUser,
    db: DbSession,
):
    payment = update_payment(db, user, obligation_id, payment_id, payload)
    return {"id": str(payment.id)}


@router.delete(
    "/obligations/{obligation_id}/payments/{payment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_payment(
    obligation_id: uuid.UUID,
    payment_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    delete_payment(db, user, obligation_id, payment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("", response_model=FinancialCalendarResponse)
def get_calendar(user: CurrentUser, db: DbSession, days: Annotated[int, Query(ge=1, le=120)] = 45):
    today = datetime.now(ZoneInfo(user.timezone)).date()
    return calendar_view(db, user, today=today, days=days)
