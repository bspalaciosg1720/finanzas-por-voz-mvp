import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.savings.models import SavingsContribution, SavingsGoal
from app.modules.savings.schemas import (
    SavingsContributionCreate,
    SavingsContributionResponse,
    SavingsContributionUpdate,
    SavingsGoalCreate,
    SavingsGoalResponse,
    SavingsGoalUpdate,
)
from app.modules.transactions.linked import (
    add_linked_transaction,
    update_linked_transaction,
    void_linked_transaction,
)
from app.modules.users.models import User


def create_goal(db: Session, user: User, payload: SavingsGoalCreate) -> SavingsGoal:
    if payload.currency != user.default_currency:
        raise AppError(
            status=422,
            title="Unsupported goal currency",
            detail="Savings goals currently use the account's default currency.",
            error_type="unsupported-goal-currency",
        )
    goal = SavingsGoal(user_id=user.id, **payload.model_dump())
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_goal(db: Session, user: User, goal_id: uuid.UUID) -> SavingsGoal:
    goal = db.scalar(
        select(SavingsGoal).where(
            SavingsGoal.id == goal_id,
            SavingsGoal.user_id == user.id,
            SavingsGoal.status != "archived",
        )
    )
    if goal is None:
        raise AppError(
            status=404,
            title="Savings goal not found",
            detail="The requested savings goal does not exist.",
            error_type="savings-goal-not-found",
        )
    return goal


def update_goal(
    db: Session,
    user: User,
    goal_id: uuid.UUID,
    payload: SavingsGoalUpdate,
) -> SavingsGoal:
    goal = get_goal(db, user, goal_id)
    values = payload.model_dump(exclude_unset=True)
    for field, value in values.items():
        setattr(goal, field, value)
    db.commit()
    db.refresh(goal)
    return goal


def archive_goal(db: Session, user: User, goal_id: uuid.UUID) -> None:
    goal = get_goal(db, user, goal_id)
    goal.status = "archived"
    db.commit()


def add_contribution(
    db: Session,
    user: User,
    goal_id: uuid.UUID,
    payload: SavingsContributionCreate,
) -> SavingsContribution:
    goal = get_goal(db, user, goal_id)
    transaction = add_linked_transaction(
        db,
        user,
        movement_type="expense",
        amount_minor=payload.amount_minor,
        occurred_at=payload.contributed_at,
        description=f"Aporte a meta: {goal.name}",
        financial_role="savings_transfer",
    )
    contribution = SavingsContribution(
        goal_id=goal_id,
        user_id=user.id,
        transaction_id=transaction.id,
        **payload.model_dump(),
    )
    db.add(contribution)
    db.commit()
    db.refresh(contribution)
    refresh_goal_status(db, user, goal_id)
    return contribution


def delete_contribution(
    db: Session,
    user: User,
    goal_id: uuid.UUID,
    contribution_id: uuid.UUID,
) -> None:
    get_goal(db, user, goal_id)
    contribution = db.scalar(
        select(SavingsContribution).where(
            SavingsContribution.id == contribution_id,
            SavingsContribution.goal_id == goal_id,
            SavingsContribution.user_id == user.id,
        )
    )
    if contribution is None:
        raise AppError(
            status=404,
            title="Contribution not found",
            detail="The requested contribution does not exist.",
            error_type="contribution-not-found",
        )
    void_linked_transaction(db, user, contribution.transaction_id)
    db.delete(contribution)
    db.commit()
    refresh_goal_status(db, user, goal_id)


def update_contribution(
    db: Session,
    user: User,
    goal_id: uuid.UUID,
    contribution_id: uuid.UUID,
    payload: SavingsContributionUpdate,
) -> SavingsContribution:
    goal = get_goal(db, user, goal_id)
    contribution = db.scalar(
        select(SavingsContribution).where(
            SavingsContribution.id == contribution_id,
            SavingsContribution.goal_id == goal.id,
            SavingsContribution.user_id == user.id,
        )
    )
    if contribution is None:
        raise AppError(
            status=404,
            title="Contribution not found",
            detail="The requested contribution does not exist.",
            error_type="contribution-not-found",
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(contribution, field, value)
    update_linked_transaction(
        db,
        user,
        contribution.transaction_id,
        movement_type="expense",
        amount_minor=contribution.amount_minor,
        occurred_at=contribution.contributed_at,
        description=f"Aporte a meta: {goal.name}",
    )
    db.commit()
    db.refresh(contribution)
    refresh_goal_status(db, user, goal_id)
    return contribution


def refresh_goal_status(
    db: Session,
    user: User,
    goal_id: uuid.UUID,
) -> None:
    goal = get_goal(db, user, goal_id)
    saved = contribution_total(db, user, goal_id)
    goal.status = "completed" if saved >= goal.target_amount_minor else "active"
    db.commit()


def contribution_total(db: Session, user: User, goal_id: uuid.UUID) -> int:
    return int(
        db.scalar(
            select(func.coalesce(func.sum(SavingsContribution.amount_minor), 0)).where(
                SavingsContribution.goal_id == goal_id,
                SavingsContribution.user_id == user.id,
            )
        )
        or 0
    )


def list_goals(db: Session, user: User) -> list[SavingsGoalResponse]:
    goals = list(
        db.scalars(
            select(SavingsGoal)
            .where(
                SavingsGoal.user_id == user.id,
                SavingsGoal.status != "archived",
            )
            .order_by(SavingsGoal.created_at.desc())
        )
    )
    responses = []
    for goal in goals:
        contributions = list(
            db.scalars(
                select(SavingsContribution)
                .where(
                    SavingsContribution.goal_id == goal.id,
                    SavingsContribution.user_id == user.id,
                )
                .order_by(SavingsContribution.contributed_at.desc())
            )
        )
        saved = sum(item.amount_minor for item in contributions)
        responses.append(
            SavingsGoalResponse(
                id=goal.id,
                name=goal.name,
                goal_type=goal.goal_type,
                target_amount_minor=goal.target_amount_minor,
                saved_amount_minor=saved,
                currency=goal.currency,
                target_date=goal.target_date,
                planned_monthly_minor=goal.planned_monthly_minor,
                status=goal.status,
                progress_percent=round((saved / goal.target_amount_minor) * 100, 1),
                contributions=[
                    SavingsContributionResponse(
                        id=item.id,
                        amount_minor=item.amount_minor,
                        contributed_at=item.contributed_at,
                        note=item.note,
                    )
                    for item in contributions
                ],
            )
        )
    return responses
