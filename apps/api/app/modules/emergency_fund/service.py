import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.categories.models import Category
from app.modules.emergency_fund.models import EmergencyFund, EmergencyFundEvent
from app.modules.emergency_fund.schemas import (
    EmergencyFundEventCreate,
    EmergencyFundEventUpdate,
    EmergencyFundResponse,
)
from app.modules.financial_health.classification import ESSENTIAL_SLUGS
from app.modules.transactions.linked import (
    add_linked_transaction,
    find_idempotent_transaction,
    linked_fingerprint,
    update_linked_transaction,
    void_linked_transaction,
)
from app.modules.transactions.models import Transaction
from app.modules.users.models import User


def get_or_create_fund(db: Session, user: User) -> EmergencyFund:
    fund = db.get(EmergencyFund, user.id)
    if fund is None:
        fund = EmergencyFund(user_id=user.id, currency=user.default_currency)
        db.add(fund)
        db.commit()
        db.refresh(fund)
    return fund


def essential_expenses(db: Session, user: User, start: datetime, end: datetime) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(Transaction.amount_minor), 0))
            .join(Category, Category.id == Transaction.category_id)
            .where(
                Transaction.user_id == user.id,
                Transaction.currency == user.default_currency,
                Transaction.type == "expense",
                Transaction.status == "confirmed",
                Transaction.deleted_at.is_(None),
                Category.slug.in_(ESSENTIAL_SLUGS),
                Transaction.occurred_at >= start,
                Transaction.occurred_at < end,
            )
        )
        or 0
    )


def fund_response(db: Session, user: User, start: datetime, end: datetime) -> EmergencyFundResponse:
    fund = get_or_create_fund(db, user)
    essential = essential_expenses(db, user, start, end)
    target = essential * fund.target_months
    events = list(
        db.scalars(
            select(EmergencyFundEvent)
            .where(EmergencyFundEvent.user_id == user.id)
            .order_by(EmergencyFundEvent.occurred_at.desc())
            .limit(20)
        )
    )
    return EmergencyFundResponse(
        currency=fund.currency,
        target_months=fund.target_months,
        balance_minor=fund.balance_minor,
        pending_replenishment_minor=fund.pending_replenishment_minor,
        essential_expense_minor=essential,
        target_amount_minor=target,
        coverage_months=round(fund.balance_minor / essential, 2) if essential else None,
        progress_percent=round(fund.balance_minor * 100 / target, 1) if target else None,
        events=events,
    )


def add_event(
    db: Session,
    user: User,
    payload: EmergencyFundEventCreate,
    idempotency_key: uuid.UUID,
) -> EmergencyFundEvent:
    fingerprint = linked_fingerprint("emergency_fund_event", user.id, payload)
    existing_transaction = find_idempotent_transaction(db, user, idempotency_key, fingerprint)
    if existing_transaction is not None:
        existing_event = db.scalar(
            select(EmergencyFundEvent).where(
                EmergencyFundEvent.transaction_id == existing_transaction.id,
                EmergencyFundEvent.user_id == user.id,
            )
        )
        if existing_event is not None:
            return existing_event
    fund = get_or_create_fund(db, user)
    if payload.event_type == "withdrawal" and payload.amount_minor > fund.balance_minor:
        raise AppError(
            status=422,
            title="Insufficient emergency fund",
            detail="The withdrawal cannot exceed the current balance.",
            error_type="insufficient-emergency-fund",
        )
    transaction = add_linked_transaction(
        db,
        user,
        movement_type="income" if payload.event_type == "withdrawal" else "expense",
        amount_minor=payload.amount_minor,
        occurred_at=payload.occurred_at,
        description=(
            "Retiro del fondo de emergencia"
            if payload.event_type == "withdrawal"
            else "Aporte al fondo de emergencia"
        ),
        financial_role="savings_transfer",
        idempotency_key=idempotency_key,
        idempotency_fingerprint=fingerprint,
    )
    event = EmergencyFundEvent(
        user_id=user.id, transaction_id=transaction.id, **payload.model_dump()
    )
    if payload.event_type == "withdrawal":
        fund.balance_minor -= payload.amount_minor
        fund.pending_replenishment_minor += payload.amount_minor
    else:
        fund.balance_minor += payload.amount_minor
        fund.pending_replenishment_minor = max(
            0, fund.pending_replenishment_minor - payload.amount_minor
        )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_event(db: Session, user: User, event_id) -> EmergencyFundEvent:
    event = db.scalar(
        select(EmergencyFundEvent).where(
            EmergencyFundEvent.id == event_id,
            EmergencyFundEvent.user_id == user.id,
        )
    )
    if event is None:
        raise AppError(
            status=404,
            title="Fund event not found",
            detail="The emergency fund event does not exist.",
            error_type="fund-event-not-found",
        )
    return event


def recalculate_fund(db: Session, user: User) -> EmergencyFund:
    fund = get_or_create_fund(db, user)
    balance = pending = 0
    events = list(
        db.scalars(
            select(EmergencyFundEvent)
            .where(EmergencyFundEvent.user_id == user.id)
            .order_by(EmergencyFundEvent.occurred_at, EmergencyFundEvent.created_at)
        )
    )
    for event in events:
        if event.event_type == "deposit":
            balance += event.amount_minor
            pending = max(0, pending - event.amount_minor)
        else:
            if event.amount_minor > balance:
                raise AppError(
                    status=422,
                    title="Invalid fund history",
                    detail=(
                        "This change would make a withdrawal exceed the available "
                        "balance at that date."
                    ),
                    error_type="invalid-fund-history",
                )
            balance -= event.amount_minor
            pending += event.amount_minor
    fund.balance_minor = balance
    fund.pending_replenishment_minor = pending
    return fund


def update_event(
    db: Session,
    user: User,
    event_id,
    payload: EmergencyFundEventUpdate,
) -> EmergencyFundEvent:
    event = get_event(db, user, event_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    update_linked_transaction(
        db,
        user,
        event.transaction_id,
        movement_type="income" if event.event_type == "withdrawal" else "expense",
        amount_minor=event.amount_minor,
        occurred_at=event.occurred_at,
        description=(
            "Retiro del fondo de emergencia"
            if event.event_type == "withdrawal"
            else "Aporte al fondo de emergencia"
        ),
    )
    recalculate_fund(db, user)
    db.commit()
    db.refresh(event)
    return event


def delete_event(db: Session, user: User, event_id) -> None:
    event = get_event(db, user, event_id)
    void_linked_transaction(db, user, event.transaction_id)
    db.delete(event)
    db.flush()
    recalculate_fund(db, user)
    db.commit()
