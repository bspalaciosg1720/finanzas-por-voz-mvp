import hmac
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.transaction_suggestions.schemas import (
    InboundEmailPayload,
    InboxAddressResponse,
    SuggestionConfirm,
    SuggestionResponse,
)
from app.modules.transaction_suggestions.service import (
    confirm_suggestion,
    discard_suggestion,
    get_or_create_inbox,
    ingest_email,
    list_pending,
)

router = APIRouter(prefix="/transaction-suggestions", tags=["Transaction suggestions"])
DbSession = Annotated[Session, Depends(get_db)]


def require_inbound_email_enabled() -> None:
    if not get_settings().inbound_email_enabled:
        raise AppError(
            status=404,
            title="Integration unavailable",
            detail="Inbound email integration is not enabled.",
            error_type="integration-unavailable",
        )


@router.get("/inbox", response_model=InboxAddressResponse)
def inbox(
    user: CurrentUser,
    db: DbSession,
    _: Annotated[None, Depends(require_inbound_email_enabled)],
) -> InboxAddressResponse:
    return InboxAddressResponse(address=get_or_create_inbox(db, user))


@router.get("", response_model=list[SuggestionResponse])
def suggestions(user: CurrentUser, db: DbSession) -> list[SuggestionResponse]:
    return [SuggestionResponse.model_validate(item) for item in list_pending(db, user)]


@router.post("/inbound-email", response_model=SuggestionResponse | None)
def inbound_email(
    payload: InboundEmailPayload,
    db: DbSession,
    secret: Annotated[str, Header(alias="X-Inbound-Email-Secret")],
    _: Annotated[None, Depends(require_inbound_email_enabled)],
) -> SuggestionResponse | None:
    if not hmac.compare_digest(secret, get_settings().inbound_email_secret):
        raise AppError(
            status=401,
            title="Invalid webhook secret",
            detail="Webhook authentication failed.",
            error_type="invalid-webhook-secret",
        )
    result = ingest_email(db, payload)
    return SuggestionResponse.model_validate(result) if result else None


@router.post("/{suggestion_id}/confirm", response_model=SuggestionResponse)
def confirm(
    suggestion_id: uuid.UUID,
    payload: SuggestionConfirm,
    user: CurrentUser,
    db: DbSession,
) -> SuggestionResponse:
    return SuggestionResponse.model_validate(confirm_suggestion(db, user, suggestion_id, payload))


@router.post("/{suggestion_id}/discard", response_model=SuggestionResponse)
def discard(suggestion_id: uuid.UUID, user: CurrentUser, db: DbSession) -> SuggestionResponse:
    return SuggestionResponse.model_validate(discard_suggestion(db, user, suggestion_id))
