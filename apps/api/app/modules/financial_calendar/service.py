import calendar
import uuid
from datetime import date, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.categories.models import Category
from app.modules.financial_calendar.models import FinancialObligation, ObligationPayment
from app.modules.financial_calendar.schemas import (
    CalendarItem,
    FinancialCalendarResponse,
    ObligationCreate,
    ObligationPaymentCreate,
    ObligationPaymentUpdate,
    ObligationUpdate,
)
from app.modules.transactions.linked import (
    add_linked_transaction,
    find_idempotent_transaction,
    linked_fingerprint,
    update_linked_transaction,
    void_linked_transaction,
)
from app.modules.users.models import User


def due_date_for(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def create_obligation(db: Session, user: User, payload: ObligationCreate) -> FinancialObligation:
    if payload.currency != user.default_currency:
        raise AppError(
            status=422,
            title="Unsupported currency",
            detail="Obligations use the account currency.",
            error_type="unsupported-obligation-currency",
        )
    validate_expense_category(db, user, payload.category_id)
    item = FinancialObligation(user_id=user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def list_obligations(db: Session, user: User):
    return list(
        db.scalars(
            select(FinancialObligation)
            .where(FinancialObligation.user_id == user.id, FinancialObligation.is_active.is_(True))
            .order_by(FinancialObligation.due_day, FinancialObligation.name)
        )
    )


def get_obligation(db: Session, user: User, obligation_id: uuid.UUID) -> FinancialObligation:
    item = db.scalar(
        select(FinancialObligation).where(
            FinancialObligation.id == obligation_id,
            FinancialObligation.user_id == user.id,
            FinancialObligation.is_active.is_(True),
        )
    )
    if item is None:
        raise AppError(
            status=404,
            title="Obligation not found",
            detail="The obligation does not exist.",
            error_type="obligation-not-found",
        )
    return item


def update_obligation(
    db: Session, user: User, obligation_id: uuid.UUID, payload: ObligationUpdate
) -> FinancialObligation:
    item = get_obligation(db, user, obligation_id)
    values = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "category_id" in values:
        validate_expense_category(db, user, values["category_id"])
    for field, value in values.items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


def archive_obligation(db: Session, user: User, obligation_id: uuid.UUID) -> None:
    item = get_obligation(db, user, obligation_id)
    item.is_active = False
    db.commit()


def add_payment(
    db: Session,
    user: User,
    obligation_id: uuid.UUID,
    payload: ObligationPaymentCreate,
    idempotency_key: uuid.UUID,
):
    fingerprint = linked_fingerprint("obligation_payment", obligation_id, payload)
    existing_transaction = find_idempotent_transaction(db, user, idempotency_key, fingerprint)
    if existing_transaction is not None:
        existing_payment = db.scalar(
            select(ObligationPayment).where(
                ObligationPayment.transaction_id == existing_transaction.id,
                ObligationPayment.user_id == user.id,
            )
        )
        if existing_payment is not None:
            return existing_payment
    item = get_obligation(db, user, obligation_id)
    transaction = add_linked_transaction(
        db,
        user,
        movement_type="expense",
        amount_minor=payload.amount_minor,
        occurred_at=payload.paid_at,
        description=f"Pago de obligación: {item.name}",
        financial_role="obligation_payment",
        category_id=item.category_id,
        idempotency_key=idempotency_key,
        idempotency_fingerprint=fingerprint,
    )
    payment = ObligationPayment(
        obligation_id=item.id,
        user_id=user.id,
        transaction_id=transaction.id,
        category_id=item.category_id,
        **payload.model_dump(),
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payment(
    db: Session, user: User, obligation_id: uuid.UUID, payment_id: uuid.UUID
) -> tuple[FinancialObligation, ObligationPayment]:
    obligation = db.scalar(
        select(FinancialObligation).where(
            FinancialObligation.id == obligation_id,
            FinancialObligation.user_id == user.id,
        )
    )
    payment = db.scalar(
        select(ObligationPayment).where(
            ObligationPayment.id == payment_id,
            ObligationPayment.obligation_id == obligation_id,
            ObligationPayment.user_id == user.id,
        )
    )
    if obligation is None or payment is None:
        raise AppError(
            status=404,
            title="Payment not found",
            detail="The obligation payment does not exist.",
            error_type="obligation-payment-not-found",
        )
    return obligation, payment


def update_payment(
    db: Session,
    user: User,
    obligation_id: uuid.UUID,
    payment_id: uuid.UUID,
    payload: ObligationPaymentUpdate,
) -> ObligationPayment:
    obligation, payment = get_payment(db, user, obligation_id, payment_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(payment, field, value)
    update_linked_transaction(
        db,
        user,
        payment.transaction_id,
        movement_type="expense",
        amount_minor=payment.amount_minor,
        occurred_at=payment.paid_at,
        description=f"Pago de obligación: {obligation.name}",
        category_id=payment.category_id,
    )
    db.commit()
    db.refresh(payment)
    return payment


def delete_payment(
    db: Session, user: User, obligation_id: uuid.UUID, payment_id: uuid.UUID
) -> None:
    _, payment = get_payment(db, user, obligation_id, payment_id)
    void_linked_transaction(db, user, payment.transaction_id)
    db.delete(payment)
    db.commit()


def calendar_view(
    db: Session, user: User, *, today: date, days: int = 45
) -> FinancialCalendarResponse:
    end = today + timedelta(days=days)
    obligations = list_obligations(db, user)
    payments = {
        (item.obligation_id, item.due_date): item
        for item in db.scalars(
            select(ObligationPayment).where(ObligationPayment.user_id == user.id)
        )
    }
    items = []
    for obligation in obligations:
        cursor = date(today.year, today.month, 1)
        while cursor <= end:
            due = due_date_for(cursor.year, cursor.month, obligation.due_day)
            if today <= due <= end:
                payment = payments.get((obligation.id, due))
                payment_id = payment.id if payment else None
                category_id = payment.category_id if payment else obligation.category_id
                category = db.get(Category, category_id) if category_id else None
                items.append(
                    CalendarItem(
                        obligation_id=obligation.id,
                        name=obligation.name,
                        obligation_type=obligation.obligation_type,
                        amount_minor=obligation.amount_minor,
                        currency=obligation.currency,
                        due_date=due,
                        days_until_due=(due - today).days,
                        status="paid" if payment else "upcoming",
                        payment_id=payment_id,
                        category_id=category_id,
                        category_name=category.name if category else "Sin categoría",
                    )
                )
            cursor = (
                date(cursor.year + 1, 1, 1)
                if cursor.month == 12
                else date(cursor.year, cursor.month + 1, 1)
            )
    items.sort(key=lambda item: (item.due_date, item.name))
    week_totals: dict[str, int] = {}
    for item in items:
        if item.status != "paid":
            key = f"{item.due_date.isocalendar().year}-W{item.due_date.isocalendar().week:02d}"
            week_totals[key] = week_totals.get(key, 0) + item.amount_minor
    monthly_income_threshold = (
        sum(item.amount_minor for item in items if item.status != "paid") * 0.4
    )
    concentrated = [
        key
        for key, amount in week_totals.items()
        if len(items) >= 2 and amount >= monthly_income_threshold
    ]
    return FinancialCalendarResponse(items=items, concentrated_weeks=concentrated)


def validate_expense_category(db: Session, user: User, category_id: uuid.UUID) -> Category:
    category = db.scalar(
        select(Category).where(
            Category.id == category_id,
            Category.is_active.is_(True),
            Category.movement_scope.in_(("expense", "both")),
            or_(Category.user_id.is_(None), Category.user_id == user.id),
        )
    )
    if category is None:
        raise AppError(
            status=422,
            title="Invalid obligation category",
            detail="Choose an active expense category available to this account.",
            error_type="invalid-obligation-category",
        )
    return category
