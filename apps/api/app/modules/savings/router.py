import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.savings.schemas import (
    SavingsContributionCreate,
    SavingsContributionResponse,
    SavingsContributionUpdate,
    SavingsGoalCreate,
    SavingsGoalResponse,
    SavingsGoalUpdate,
)
from app.modules.savings.service import (
    add_contribution,
    archive_goal,
    create_goal,
    delete_contribution,
    list_goals,
    update_contribution,
    update_goal,
)

router = APIRouter(prefix="/savings-goals", tags=["Savings goals"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[SavingsGoalResponse])
def get_goals(user: CurrentUser, db: DbSession) -> list[SavingsGoalResponse]:
    return list_goals(db, user)


@router.post("", status_code=status.HTTP_201_CREATED)
def add_goal(
    payload: SavingsGoalCreate,
    user: CurrentUser,
    db: DbSession,
) -> dict[str, str]:
    goal = create_goal(db, user, payload)
    return {"id": str(goal.id)}


@router.patch("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def edit_goal(
    goal_id: uuid.UUID,
    payload: SavingsGoalUpdate,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    update_goal(db, user, goal_id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(goal_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    archive_goal(db, user, goal_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{goal_id}/contributions",
    response_model=SavingsContributionResponse,
    status_code=status.HTTP_201_CREATED,
)
def contribute(
    goal_id: uuid.UUID,
    payload: SavingsContributionCreate,
    user: CurrentUser,
    db: DbSession,
):
    return add_contribution(db, user, goal_id, payload)


@router.delete(
    "/{goal_id}/contributions/{contribution_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_contribution(
    goal_id: uuid.UUID,
    contribution_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    delete_contribution(db, user, goal_id, contribution_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch(
    "/{goal_id}/contributions/{contribution_id}",
    response_model=SavingsContributionResponse,
)
def edit_contribution(
    goal_id: uuid.UUID,
    contribution_id: uuid.UUID,
    payload: SavingsContributionUpdate,
    user: CurrentUser,
    db: DbSession,
):
    return update_contribution(db, user, goal_id, contribution_id, payload)
