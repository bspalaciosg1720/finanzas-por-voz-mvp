import hashlib
import secrets
import uuid
from datetime import UTC
from email.utils import parseaddr

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.transaction_suggestions.models import InboundEmailAddress, TransactionSuggestion
from app.modules.transaction_suggestions.parser import parse_financial_email
from app.modules.transaction_suggestions.schemas import InboundEmailPayload, SuggestionConfirm
from app.modules.transactions.schemas import TransactionCreate
from app.modules.transactions.service import create_transaction
from app.modules.users.models import User
from app.shared.time import utc_now


def get_or_create_inbox(db: Session, user: User) -> str:
    inbox = db.get(InboundEmailAddress, user.id)
    if inbox is None:
        inbox = InboundEmailAddress(user_id=user.id, token=secrets.token_hex(24))
        db.add(inbox)
        db.commit()
    return f"movimientos+{inbox.token}@{get_settings().inbound_email_domain}"


def ingest_email(db: Session, payload: InboundEmailPayload) -> TransactionSuggestion | None:
    token = recipient_token(payload.recipient)
    inbox = db.scalar(select(InboundEmailAddress).where(InboundEmailAddress.token == token))
    if inbox is None:
        raise AppError(
            status=404,
            title="Inbox not found",
            detail="The recipient is not active.",
            error_type="inbox-not-found",
        )
    sender_address = parseaddr(payload.sender)[1].lower()
    if "@" not in sender_address:
        raise AppError(
            status=422,
            title="Invalid sender",
            detail="A valid sender is required.",
            error_type="invalid-sender",
        )
    occurred_at = payload.received_at or utc_now()
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)
    parsed = parse_financial_email(payload.subject, payload.text, occurred_at)
    if parsed is None:
        return None
    identity = payload.message_id or f"{sender_address}|{payload.subject}|{payload.text}"
    message_hash = hashlib.sha256(identity.encode()).hexdigest()
    existing = db.scalar(
        select(TransactionSuggestion).where(
            TransactionSuggestion.user_id == inbox.user_id,
            TransactionSuggestion.message_hash == message_hash,
        )
    )
    if existing:
        return existing
    suggestion = TransactionSuggestion(
        user_id=inbox.user_id,
        message_hash=message_hash,
        sender_domain=sender_address.rsplit("@", 1)[1],
        **parsed.__dict__,
    )
    db.add(suggestion)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return db.scalar(
            select(TransactionSuggestion).where(
                TransactionSuggestion.user_id == inbox.user_id,
                TransactionSuggestion.message_hash == message_hash,
            )
        )
    return suggestion


def list_pending(db: Session, user: User) -> list[TransactionSuggestion]:
    return list(
        db.scalars(
            select(TransactionSuggestion)
            .where(
                TransactionSuggestion.user_id == user.id, TransactionSuggestion.status == "pending"
            )
            .order_by(TransactionSuggestion.created_at.desc())
            .limit(50)
        )
    )


def resolve_suggestion(db: Session, user: User, suggestion_id: uuid.UUID) -> TransactionSuggestion:
    suggestion = db.scalar(
        select(TransactionSuggestion).where(
            TransactionSuggestion.id == suggestion_id,
            TransactionSuggestion.user_id == user.id,
        )
    )
    if suggestion is None:
        raise AppError(
            status=404,
            title="Suggestion not found",
            detail="The suggestion does not exist.",
            error_type="suggestion-not-found",
        )
    return suggestion


def confirm_suggestion(
    db: Session, user: User, suggestion_id: uuid.UUID, changes: SuggestionConfirm
) -> TransactionSuggestion:
    suggestion = resolve_suggestion(db, user, suggestion_id)
    if suggestion.status == "confirmed":
        return suggestion
    if suggestion.status != "pending":
        raise AppError(
            status=409,
            title="Suggestion resolved",
            detail="This suggestion was already discarded.",
            error_type="suggestion-resolved",
        )
    values = changes.model_dump(exclude_unset=True)
    occurred_at = values.get("occurred_at", suggestion.occurred_at)
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=UTC)
    payload = TransactionCreate(
        type=values.get("type", suggestion.type),
        amount_minor=values.get("amount_minor", suggestion.amount_minor),
        currency=suggestion.currency,
        category_id=values.get("category_id"),
        description=values.get("description", suggestion.description),
        occurred_at=occurred_at,
        source="integration",
    )
    transaction = create_transaction(db, user, payload, suggestion.id)
    suggestion.transaction_id = transaction.id
    suggestion.status = "confirmed"
    suggestion.resolved_at = utc_now()
    db.commit()
    return suggestion


def discard_suggestion(db: Session, user: User, suggestion_id: uuid.UUID) -> TransactionSuggestion:
    suggestion = resolve_suggestion(db, user, suggestion_id)
    if suggestion.status == "pending":
        suggestion.status = "discarded"
        suggestion.resolved_at = utc_now()
        db.commit()
    return suggestion


def recipient_token(recipient: str) -> str:
    address = parseaddr(recipient)[1]
    local = address.split("@", 1)[0]
    if not local.startswith("movimientos+") or len(local) <= len("movimientos+"):
        raise AppError(
            status=422,
            title="Invalid recipient",
            detail="The recipient alias is invalid.",
            error_type="invalid-recipient",
        )
    return local.split("+", 1)[1]
