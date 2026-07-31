import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.transactions.models import Transaction
from app.modules.transactions.schemas import (
    TransactionCreate,
    TransactionPage,
    TransactionResponse,
    TransactionUpdate,
)
from app.modules.transactions.service import (
    create_transaction,
    delete_transaction,
    get_transaction,
    list_transactions,
    restore_transaction,
    update_transaction,
)

router = APIRouter(prefix="/transactions", tags=["Transactions"])
DbSession = Annotated[Session, Depends(get_db)]
IdempotencyKey = Annotated[uuid.UUID, Header(alias="Idempotency-Key")]


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def add_transaction(
    payload: TransactionCreate,
    idempotency_key: IdempotencyKey,
    user: CurrentUser,
    db: DbSession,
) -> Transaction:
    return create_transaction(db, user, payload, idempotency_key)


@router.get("", response_model=TransactionPage)
def get_transactions(
    user: CurrentUser,
    db: DbSession,
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    movement_type: Annotated[
        str | None,
        Query(alias="type", pattern=r"^(income|expense)$"),
    ] = None,
    category_id: uuid.UUID | None = None,
    query: Annotated[str | None, Query(max_length=100)] = None,
    cursor: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 30,
) -> TransactionPage:
    items, next_cursor = list_transactions(
        db,
        user,
        date_from=date_from,
        date_to=date_to,
        movement_type=movement_type,
        category_id=category_id,
        query=query,
        cursor=cursor,
        limit=limit,
    )
    return TransactionPage(
        items=[TransactionResponse.model_validate(item) for item in items],
        next_cursor=next_cursor,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction_detail(
    transaction_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Transaction:
    return get_transaction(db, user, transaction_id)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def edit_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    user: CurrentUser,
    db: DbSession,
) -> Transaction:
    return update_transaction(db, user, transaction_id, payload)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_transaction(
    transaction_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    delete_transaction(db, user, transaction_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{transaction_id}/restore", response_model=TransactionResponse)
def restore_deleted_transaction(
    transaction_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Transaction:
    return restore_transaction(db, user, transaction_id)
