from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.financial_alerts.schemas import FinancialAlertDismiss, FinancialAlertsResponse
from app.modules.financial_alerts.service import dismiss_alert, get_alerts

router = APIRouter(prefix="/financial-alerts", tags=["Financial alerts"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=FinancialAlertsResponse)
def financial_alerts(
    user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=5)] = 3,
) -> FinancialAlertsResponse:
    return get_alerts(db, user, limit=limit)


@router.post("/dismiss", status_code=status.HTTP_204_NO_CONTENT)
def dismiss(payload: FinancialAlertDismiss, user: CurrentUser, db: DbSession) -> Response:
    dismiss_alert(db, user, payload.key)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
