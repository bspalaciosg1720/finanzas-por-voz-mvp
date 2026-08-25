import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.debts.schemas import (
    DebtCreate,
    DebtPaymentCreate,
    DebtPaymentResponse,
    DebtPaymentUpdate,
    DebtResponse,
    DebtUpdate,
    PayoffComparison,
    PayoffPlan,
)
from app.modules.debts.service import (
    add_payment,
    archive_debt,
    create_debt,
    debt_response,
    delete_payment,
    list_debts,
    payoff_plan,
    update_debt,
    update_payment,
)

router = APIRouter(prefix="/debts", tags=["Debts"])
DbSession = Annotated[Session, Depends(get_db)]
IdempotencyKey = Annotated[uuid.UUID, Header(alias="Idempotency-Key")]


@router.get("", response_model=list[DebtResponse])
def get_debts(user: CurrentUser, db: DbSession) -> list[DebtResponse]:
    return list_debts(db, user)


@router.post("", response_model=DebtResponse, status_code=status.HTTP_201_CREATED)
def add_debt(payload: DebtCreate, user: CurrentUser, db: DbSession) -> DebtResponse:
    debt = create_debt(db, user, payload)
    return debt_response(db, user, debt)


@router.get("/payoff-plan", response_model=PayoffPlan)
def get_payoff_plan(
    user: CurrentUser,
    db: DbSession,
    strategy: Annotated[str, Query(pattern=r"^(snowball|avalanche|hybrid)$")] = "snowball",
    extra_payment_minor: Annotated[int, Query(ge=0, le=9_000_000_000_000_000)] = 0,
) -> PayoffPlan:
    return payoff_plan(db, user, strategy=strategy, extra_payment_minor=extra_payment_minor)


@router.get("/payoff-comparison", response_model=PayoffComparison)
def compare_payoff_plans(
    user: CurrentUser,
    db: DbSession,
    extra_payment_minor: Annotated[int, Query(ge=0, le=9_000_000_000_000_000)] = 0,
) -> PayoffComparison:
    snowball = payoff_plan(db, user, strategy="snowball", extra_payment_minor=extra_payment_minor)
    avalanche = payoff_plan(db, user, strategy="avalanche", extra_payment_minor=extra_payment_minor)
    if snowball.estimated_interest_minor is None or avalanche.estimated_interest_minor is None:
        recommendation = savings = None
    else:
        savings = snowball.estimated_interest_minor - avalanche.estimated_interest_minor
        recommendation = "avalanche" if savings > 0 else "snowball"
    return PayoffComparison(
        snowball=snowball,
        avalanche=avalanche,
        recommended_strategy=recommendation,
        interest_savings_minor=savings,
    )


@router.patch("/{debt_id}", status_code=status.HTTP_204_NO_CONTENT)
def edit_debt(
    debt_id: uuid.UUID, payload: DebtUpdate, user: CurrentUser, db: DbSession
) -> Response:
    update_debt(db, user, debt_id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{debt_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_debt(debt_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    archive_debt(db, user, debt_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{debt_id}/payments", response_model=DebtPaymentResponse, status_code=status.HTTP_201_CREATED
)
def register_payment(
    debt_id: uuid.UUID,
    payload: DebtPaymentCreate,
    user: CurrentUser,
    db: DbSession,
    idempotency_key: IdempotencyKey,
):
    return add_payment(db, user, debt_id, payload, idempotency_key)


@router.patch("/{debt_id}/payments/{payment_id}", response_model=DebtPaymentResponse)
def edit_payment(
    debt_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: DebtPaymentUpdate,
    user: CurrentUser,
    db: DbSession,
):
    return update_payment(db, user, debt_id, payment_id, payload)


@router.delete("/{debt_id}/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_payment(
    debt_id: uuid.UUID,
    payment_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    delete_payment(db, user, debt_id, payment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
