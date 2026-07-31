import base64
import binascii
import hashlib
import json
import uuid
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.categories.models import Category
from app.modules.transactions.models import Transaction
from app.modules.transactions.schemas import TransactionCreate, TransactionUpdate
from app.modules.users.models import User
from app.shared.time import utc_now


def payload_fingerprint(payload: TransactionCreate) -> str:
    canonical = json.dumps(
        payload.model_dump(mode="json"),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def create_transaction(
    db: Session,
    user: User,
    payload: TransactionCreate,
    idempotency_key: uuid.UUID,
) -> Transaction:
    fingerprint = payload_fingerprint(payload)
    existing = db.scalar(
        select(Transaction).where(
            Transaction.user_id == user.id,
            Transaction.idempotency_key == idempotency_key,
        )
    )
    if existing is not None:
        ensure_matching_fingerprint(existing, fingerprint)
        try_evaluate_budget_alert(db, user, existing)
        return existing

    validate_category(db, user, payload.category_id)
    transaction = Transaction(
        user_id=user.id,
        idempotency_key=idempotency_key,
        idempotency_fingerprint=fingerprint,
        **payload.model_dump(),
    )
    db.add(transaction)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Transaction).where(
                Transaction.user_id == user.id,
                Transaction.idempotency_key == idempotency_key,
            )
        )
        if existing is None:
            raise
        ensure_matching_fingerprint(existing, fingerprint)
        try_evaluate_budget_alert(db, user, existing)
        return existing
    try_evaluate_budget_alert(db, user, transaction)
    return transaction


def get_transaction(
    db: Session,
    user: User,
    transaction_id: uuid.UUID,
    *,
    include_deleted: bool = False,
) -> Transaction:
    conditions = [
        Transaction.id == transaction_id,
        Transaction.user_id == user.id,
    ]
    if not include_deleted:
        conditions.append(Transaction.deleted_at.is_(None))
    transaction = db.scalar(select(Transaction).where(*conditions))
    if transaction is None:
        raise transaction_not_found()
    return transaction


def update_transaction(
    db: Session,
    user: User,
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
) -> Transaction:
    transaction = get_transaction(db, user, transaction_id)
    values = payload.model_dump(exclude_unset=True)
    if "category_id" in values:
        validate_category(db, user, values["category_id"])
    for field, value in values.items():
        if value is not None or field == "category_id":
            setattr(transaction, field, value)
    db.commit()
    return transaction


def delete_transaction(db: Session, user: User, transaction_id: uuid.UUID) -> None:
    transaction = get_transaction(db, user, transaction_id)
    transaction.deleted_at = utc_now()
    transaction.status = "deleted"
    db.commit()


def restore_transaction(db: Session, user: User, transaction_id: uuid.UUID) -> Transaction:
    transaction = get_transaction(db, user, transaction_id, include_deleted=True)
    transaction.deleted_at = None
    transaction.status = "confirmed"
    db.commit()
    try_evaluate_budget_alert(db, user, transaction)
    return transaction


def try_evaluate_budget_alert(
    db: Session,
    user: User,
    transaction: Transaction,
) -> None:
    if transaction.type != "expense" or transaction.deleted_at is not None:
        return
    try:
        from app.modules.budgets.alerts import evaluate_budget_alert

        evaluate_budget_alert(
            db,
            user,
            category_id=transaction.category_id,
            currency=transaction.currency,
            occurred_at=transaction.occurred_at,
        )
    except SQLAlchemyError:
        db.rollback()


def list_transactions(
    db: Session,
    user: User,
    *,
    date_from: date | None,
    date_to: date | None,
    movement_type: str | None,
    category_id: uuid.UUID | None,
    query: str | None,
    cursor: str | None,
    limit: int,
) -> tuple[list[Transaction], str | None]:
    conditions = [Transaction.user_id == user.id, Transaction.deleted_at.is_(None)]
    user_timezone = ZoneInfo(user.timezone)
    if date_from:
        conditions.append(
            Transaction.occurred_at >= datetime.combine(date_from, time.min, user_timezone)
        )
    if date_to:
        conditions.append(
            Transaction.occurred_at
            < datetime.combine(date_to + timedelta(days=1), time.min, user_timezone)
        )
    if movement_type:
        conditions.append(Transaction.type == movement_type)
    if category_id:
        conditions.append(Transaction.category_id == category_id)
    if query:
        conditions.append(Transaction.description.ilike(f"%{query.strip()}%"))
    if cursor:
        cursor_date, cursor_id = decode_cursor(cursor)
        conditions.append(
            or_(
                Transaction.occurred_at < cursor_date,
                and_(
                    Transaction.occurred_at == cursor_date,
                    Transaction.id < cursor_id,
                ),
            )
        )

    items = list(
        db.scalars(
            select(Transaction)
            .where(*conditions)
            .order_by(Transaction.occurred_at.desc(), Transaction.id.desc())
            .limit(limit + 1)
        )
    )
    has_more = len(items) > limit
    page = items[:limit]
    next_cursor = encode_cursor(page[-1]) if has_more and page else None
    return page, next_cursor


def validate_category(db: Session, user: User, category_id: uuid.UUID | None) -> None:
    if category_id is None:
        return
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
            or_(Category.user_id.is_(None), Category.user_id == user.id),
        )
    )
    if category is None:
        raise AppError(
            status=422,
            title="Invalid category",
            detail="Choose an active category available to this account.",
            error_type="invalid-category",
        )


def ensure_matching_fingerprint(transaction: Transaction, fingerprint: str) -> None:
    if transaction.idempotency_fingerprint != fingerprint:
        raise AppError(
            status=409,
            title="Idempotency conflict",
            detail="This idempotency key was already used with different data.",
            error_type="idempotency-conflict",
        )


def encode_cursor(transaction: Transaction) -> str:
    occurred_at = transaction.occurred_at
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)
    payload = json.dumps(
        [occurred_at.isoformat(), str(transaction.id)],
        separators=(",", ":"),
    )
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = json.loads(base64.urlsafe_b64decode(padded).decode())
        occurred_at = datetime.fromisoformat(raw[0])
        if occurred_at.tzinfo is None:
            raise ValueError
        return occurred_at, uuid.UUID(raw[1])
    except (
        ValueError,
        TypeError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        binascii.Error,
    ) as exc:
        raise AppError(
            status=422,
            title="Invalid cursor",
            detail="Restart pagination without the supplied cursor.",
            error_type="invalid-cursor",
        ) from exc


def transaction_not_found() -> AppError:
    return AppError(
        status=404,
        title="Transaction not found",
        detail="The requested transaction does not exist.",
        error_type="transaction-not-found",
    )
