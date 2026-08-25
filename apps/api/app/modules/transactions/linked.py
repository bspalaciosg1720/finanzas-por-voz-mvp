import hashlib
import json
import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.transactions.models import Transaction
from app.modules.transactions.service import ensure_matching_fingerprint
from app.modules.users.models import User
from app.shared.time import utc_now


def add_linked_transaction(
    db: Session,
    user: User,
    *,
    movement_type: str,
    amount_minor: int,
    occurred_at: datetime,
    description: str,
    financial_role: str,
    category_id: uuid.UUID | None = None,
    idempotency_key: uuid.UUID | None = None,
    idempotency_fingerprint: str | None = None,
) -> Transaction:
    key = idempotency_key or uuid.uuid4()
    fingerprint = idempotency_fingerprint or hashlib.sha256(f"linked:{key}".encode()).hexdigest()
    transaction = Transaction(
        user_id=user.id,
        type=movement_type,
        amount_minor=amount_minor,
        currency=user.default_currency,
        category_id=category_id,
        description=description,
        occurred_at=occurred_at,
        source="integration",
        financial_role=financial_role,
        status="confirmed",
        idempotency_key=key,
        idempotency_fingerprint=fingerprint,
    )
    db.add(transaction)
    db.flush()
    return transaction


def linked_fingerprint(operation: str, parent_id: uuid.UUID, payload: object) -> str:
    values = payload.model_dump(mode="json")  # type: ignore[attr-defined]
    canonical = json.dumps(
        {"operation": operation, "parent_id": str(parent_id), "payload": values},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def find_idempotent_transaction(
    db: Session, user: User, key: uuid.UUID, fingerprint: str
) -> Transaction | None:
    transaction = db.scalar(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.idempotency_key == key,
        )
    )
    if transaction is not None:
        ensure_matching_fingerprint(transaction, fingerprint)
    return transaction


def update_linked_transaction(
    db: Session,
    user: User,
    transaction_id: uuid.UUID | None,
    *,
    movement_type: str,
    amount_minor: int,
    occurred_at: datetime,
    description: str,
    category_id: uuid.UUID | None = None,
) -> None:
    transaction = db.get(Transaction, transaction_id) if transaction_id else None
    if transaction is None or transaction.user_id != user.id:
        return
    transaction.type = movement_type
    transaction.amount_minor = amount_minor
    transaction.occurred_at = occurred_at
    transaction.description = description
    transaction.category_id = category_id


def void_linked_transaction(db: Session, user: User, transaction_id: uuid.UUID | None) -> None:
    transaction = db.get(Transaction, transaction_id) if transaction_id else None
    if transaction is None or transaction.user_id != user.id:
        return
    transaction.status = "deleted"
    transaction.deleted_at = utc_now()
