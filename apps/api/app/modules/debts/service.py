import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.debts.engine import DebtProjectionInput, payoff_order, simulate_payoff
from app.modules.debts.models import Debt, DebtPayment
from app.modules.debts.schemas import (
    DebtCreate,
    DebtPaymentCreate,
    DebtPaymentResponse,
    DebtPaymentUpdate,
    DebtResponse,
    DebtUpdate,
    PayoffPlan,
    PayoffStep,
)
from app.modules.transactions.linked import (
    add_linked_transaction,
    find_idempotent_transaction,
    linked_fingerprint,
    update_linked_transaction,
    void_linked_transaction,
)
from app.modules.users.models import User


def get_debt(db: Session, user: User, debt_id: uuid.UUID) -> Debt:
    debt = db.scalar(select(Debt).where(Debt.id == debt_id, Debt.user_id == user.id))
    if debt is None:
        raise AppError(
            status=404,
            title="Debt not found",
            detail="The requested debt does not exist.",
            error_type="debt-not-found",
        )
    return debt


def create_debt(db: Session, user: User, payload: DebtCreate) -> Debt:
    if payload.currency != user.default_currency:
        raise AppError(
            status=422,
            title="Unsupported debt currency",
            detail="Debts currently use the account currency.",
            error_type="unsupported-debt-currency",
        )
    values = payload.model_dump()
    if values["current_balance_minor"] is None:
        values["current_balance_minor"] = values["initial_balance_minor"]
    debt = Debt(user_id=user.id, **values)
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


def update_debt(db: Session, user: User, debt_id: uuid.UUID, payload: DebtUpdate) -> Debt:
    debt = get_debt(db, user, debt_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(debt, field, value)
    db.commit()
    db.refresh(debt)
    return debt


def archive_debt(db: Session, user: User, debt_id: uuid.UUID) -> None:
    debt = get_debt(db, user, debt_id)
    debt.status = "archived"
    db.commit()


def add_payment(
    db: Session,
    user: User,
    debt_id: uuid.UUID,
    payload: DebtPaymentCreate,
    idempotency_key: uuid.UUID,
) -> DebtPayment:
    fingerprint = linked_fingerprint("debt_payment", debt_id, payload)
    existing_transaction = find_idempotent_transaction(db, user, idempotency_key, fingerprint)
    if existing_transaction is not None:
        existing_payment = db.scalar(
            select(DebtPayment).where(
                DebtPayment.transaction_id == existing_transaction.id,
                DebtPayment.user_id == user.id,
            )
        )
        if existing_payment is not None:
            return existing_payment
    debt = get_debt(db, user, debt_id)
    if debt.status != "active":
        raise AppError(
            status=409,
            title="Debt is not active",
            detail="Payments can only be added to active debts.",
            error_type="inactive-debt",
        )
    if payload.amount_minor > debt.current_balance_minor:
        raise AppError(
            status=422,
            title="Payment exceeds balance",
            detail="The payment cannot exceed the current balance.",
            error_type="payment-exceeds-balance",
        )
    transaction = add_linked_transaction(
        db,
        user,
        movement_type="expense",
        amount_minor=payload.amount_minor,
        occurred_at=payload.paid_at,
        description=f"Pago de deuda: {debt.name}",
        financial_role="debt_payment",
        idempotency_key=idempotency_key,
        idempotency_fingerprint=fingerprint,
    )
    payment = DebtPayment(
        debt_id=debt.id,
        user_id=user.id,
        transaction_id=transaction.id,
        **payload.model_dump(),
    )
    debt.current_balance_minor -= payload.amount_minor
    if debt.current_balance_minor == 0:
        debt.status = "paid"
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def get_payment(
    db: Session, user: User, debt_id: uuid.UUID, payment_id: uuid.UUID
) -> tuple[Debt, DebtPayment]:
    debt = get_debt(db, user, debt_id)
    payment = db.scalar(
        select(DebtPayment).where(
            DebtPayment.id == payment_id,
            DebtPayment.debt_id == debt.id,
            DebtPayment.user_id == user.id,
        )
    )
    if payment is None:
        raise AppError(
            status=404,
            title="Payment not found",
            detail="The debt payment does not exist.",
            error_type="debt-payment-not-found",
        )
    return debt, payment


def update_payment(
    db: Session, user: User, debt_id: uuid.UUID, payment_id: uuid.UUID, payload: DebtPaymentUpdate
) -> DebtPayment:
    debt, payment = get_payment(db, user, debt_id, payment_id)
    values = payload.model_dump(exclude_unset=True)
    new_amount = values.get("amount_minor", payment.amount_minor)
    restored_balance = debt.current_balance_minor + payment.amount_minor
    if new_amount > restored_balance:
        raise AppError(
            status=422,
            title="Payment exceeds balance",
            detail="The payment cannot exceed the balance before this payment.",
            error_type="payment-exceeds-balance",
        )
    debt.current_balance_minor = restored_balance - new_amount
    debt.status = "paid" if debt.current_balance_minor == 0 else "active"
    for field, value in values.items():
        setattr(payment, field, value)
    update_linked_transaction(
        db,
        user,
        payment.transaction_id,
        movement_type="expense",
        amount_minor=payment.amount_minor,
        occurred_at=payment.paid_at,
        description=f"Pago de deuda: {debt.name}",
    )
    db.commit()
    db.refresh(payment)
    return payment


def delete_payment(db: Session, user: User, debt_id: uuid.UUID, payment_id: uuid.UUID) -> None:
    debt, payment = get_payment(db, user, debt_id, payment_id)
    debt.current_balance_minor += payment.amount_minor
    debt.status = "active"
    void_linked_transaction(db, user, payment.transaction_id)
    db.delete(payment)
    db.commit()


def debt_response(db: Session, user: User, debt: Debt) -> DebtResponse:
    payments = list(
        db.scalars(
            select(DebtPayment)
            .where(
                DebtPayment.debt_id == debt.id,
                DebtPayment.user_id == user.id,
            )
            .order_by(DebtPayment.paid_at.desc())
        )
    )
    return DebtResponse(
        id=debt.id,
        name=debt.name,
        debt_type=debt.debt_type,
        initial_balance_minor=debt.initial_balance_minor,
        current_balance_minor=debt.current_balance_minor,
        minimum_payment_minor=debt.minimum_payment_minor,
        currency=debt.currency,
        annual_interest_rate_bps=debt.annual_interest_rate_bps,
        payment_day=debt.payment_day,
        statement_day=debt.statement_day,
        installment_count=debt.installment_count,
        status=debt.status,
        progress_percent=round(
            (debt.initial_balance_minor - debt.current_balance_minor)
            * 100
            / debt.initial_balance_minor,
            1,
        ),
        payments=[DebtPaymentResponse.model_validate(item) for item in payments],
    )


def list_debts(db: Session, user: User) -> list[DebtResponse]:
    debts = list(
        db.scalars(
            select(Debt)
            .where(
                Debt.user_id == user.id,
                Debt.status != "archived",
            )
            .order_by(Debt.status, Debt.created_at.desc())
        )
    )
    return [debt_response(db, user, item) for item in debts]


def payoff_plan(db: Session, user: User, *, strategy: str, extra_payment_minor: int) -> PayoffPlan:
    debts = list(
        db.scalars(
            select(Debt).where(
                Debt.user_id == user.id,
                Debt.status == "active",
                Debt.current_balance_minor > 0,
            )
        )
    )
    inputs = [
        DebtProjectionInput(
            str(item.id),
            item.name,
            item.current_balance_minor,
            item.minimum_payment_minor,
            item.annual_interest_rate_bps,
        )
        for item in debts
    ]
    ordered = payoff_order(inputs, strategy)
    projection = simulate_payoff(inputs, strategy=strategy, extra_payment_minor=extra_payment_minor)
    limitations = []
    projected_by_id = {}
    months = interest = None
    if projection is None and any(item.annual_interest_rate_bps is None for item in inputs):
        limitations.append("Faltan tasas de interés; no se estiman meses ni intereses.")
    elif projection is None and inputs:
        limitations.append("Los pagos indicados no reducen la deuda; aumenta el pago mensual.")
    elif projection:
        results, months, interest = projection
        projected_by_id = {item.id: item for item in results}
    steps = []
    for index, item in enumerate(ordered):
        result = projected_by_id.get(item.id)
        steps.append(
            PayoffStep(
                debt_id=uuid.UUID(item.id),
                name=item.name,
                order=index + 1,
                balance_minor=item.balance_minor,
                monthly_payment_minor=item.minimum_payment_minor
                + (extra_payment_minor if index == 0 else 0),
                estimated_months=result.completion_month if result else None,
                estimated_interest_minor=result.interest_minor if result else None,
            )
        )
    minimums = sum(item.minimum_payment_minor for item in inputs)
    return PayoffPlan(
        strategy=strategy,
        currency=user.default_currency,
        minimum_payments_minor=minimums,
        extra_payment_minor=extra_payment_minor,
        total_monthly_payment_minor=minimums + extra_payment_minor,
        estimated_months=months,
        estimated_interest_minor=interest,
        steps=steps,
        limitations=limitations,
    )
