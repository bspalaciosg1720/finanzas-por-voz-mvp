from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.financial_strategies.schemas import (
    StrategyAnalysisResponse,
    StrategyConfigResponse,
    StrategyConfigUpdate,
)
from app.modules.financial_strategies.service import (
    analyze_strategies,
    config_response,
    get_or_create_config,
    update_config,
)

router = APIRouter(prefix="/financial-strategies", tags=["Financial strategies"])
DbSession = Annotated[Session, Depends(get_db)]


@router.get("/config", response_model=StrategyConfigResponse)
def get_config(user: CurrentUser, db: DbSession) -> StrategyConfigResponse:
    return config_response(get_or_create_config(db, user))


@router.patch("/config", response_model=StrategyConfigResponse)
def edit_config(
    payload: StrategyConfigUpdate, user: CurrentUser, db: DbSession
) -> StrategyConfigResponse:
    return update_config(db, user, payload)


@router.get("/analysis", response_model=StrategyAnalysisResponse)
def strategy_analysis(user: CurrentUser, db: DbSession) -> StrategyAnalysisResponse:
    return analyze_strategies(db, user)
