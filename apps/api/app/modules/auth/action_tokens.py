import secrets
from datetime import UTC, timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import hash_refresh_secret
from app.modules.auth.models import AccountActionToken
from app.shared.time import utc_now


def create_action_token(
    db: Session,
    *,
    user_id,
    purpose: str,
    lifetime: timedelta,
) -> str:
    now = utc_now()
    db.execute(
        update(AccountActionToken)
        .where(
            AccountActionToken.user_id == user_id,
            AccountActionToken.purpose == purpose,
            AccountActionToken.used_at.is_(None),
        )
        .values(used_at=now)
    )
    secret = secrets.token_urlsafe(48)
    db.add(
        AccountActionToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=hash_refresh_secret(secret),
            expires_at=now + lifetime,
        )
    )
    db.flush()
    return secret


def consume_action_token(db: Session, *, secret: str, purpose: str) -> AccountActionToken:
    token = db.scalar(
        select(AccountActionToken).where(
            AccountActionToken.token_hash == hash_refresh_secret(secret),
            AccountActionToken.purpose == purpose,
        )
    )
    now = utc_now()
    expires_at = token.expires_at if token is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if token is None or token.used_at is not None or expires_at is None or expires_at <= now:
        raise AppError(
            status=400,
            title="Invalid or expired token",
            detail="Request a new link and try again.",
            error_type="invalid-action-token",
        )
    token.used_at = now
    return token
