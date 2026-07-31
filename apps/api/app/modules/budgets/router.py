import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.budgets.alerts import list_alerts, mark_alert_read
from app.modules.budgets.schemas import (
    BudgetAlertResponse,
    BudgetCreate,
    BudgetResponse,
    BudgetUpdate,
)
from app.modules.budgets.service import (
    create_budget,
    delete_budget,
    list_budget_progress,
    update_budget,
)

router = APIRouter(prefix="/budgets", tags=["Budgets"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[BudgetResponse])
def list_budgets(
    user: CurrentUser,
    db: DbSession,
    reference_at: Annotated[datetime | None, Query()] = None,
) -> list[BudgetResponse]:
    return list_budget_progress(db, user, reference=reference_at)


@router.post("", status_code=status.HTTP_201_CREATED)
def add_budget(payload: BudgetCreate, user: CurrentUser, db: DbSession) -> dict[str, str]:
    budget = create_budget(db, user, payload)
    return {"id": str(budget.id)}


@router.patch("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def edit_budget(
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    update_budget(db, user, budget_id, payload)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_budget(budget_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    delete_budget(db, user, budget_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/alerts", response_model=list[BudgetAlertResponse])
def get_budget_alerts(
    user: CurrentUser,
    db: DbSession,
    unread_only: bool = True,
) -> list[BudgetAlertResponse]:
    return list_alerts(db, user, unread_only=unread_only)


@router.patch("/alerts/{alert_id}/read", status_code=status.HTTP_204_NO_CONTENT)
def read_budget_alert(
    alert_id: uuid.UUID,
    user: CurrentUser,
    db: DbSession,
) -> Response:
    mark_alert_read(db, user, alert_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
