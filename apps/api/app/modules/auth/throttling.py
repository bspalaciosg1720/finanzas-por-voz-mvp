import hashlib
import hmac
from datetime import UTC, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.auth.models import AuthenticationThrottle
from app.shared.time import utc_now


def _aware(value):
    return value.replace(tzinfo=UTC) if value is not None and value.tzinfo is None else value


def _key(email: str, client_host: str) -> str:
    secret = get_settings().jwt_secret.encode()
    message = f"login:{email.strip().lower()}:{client_host}".encode()
    return hmac.new(secret, message, hashlib.sha256).hexdigest()


def assert_login_allowed(db: Session, email: str, client_host: str) -> None:
    throttle = db.get(AuthenticationThrottle, _key(email, client_host))
    blocked_until = _aware(throttle.blocked_until) if throttle is not None else None
    if blocked_until is not None and blocked_until > utc_now():
        raise AppError(
            status=429,
            title="Too many attempts",
            detail="Wait before trying to sign in again.",
            error_type="too-many-login-attempts",
        )


def record_login_failure(db: Session, email: str, client_host: str) -> None:
    settings = get_settings()
    now = utc_now()
    key_hash = _key(email, client_host)
    throttle = db.get(AuthenticationThrottle, key_hash)
    window = timedelta(minutes=settings.login_block_minutes)
    if throttle is None:
        throttle = AuthenticationThrottle(
            key_hash=key_hash,
            failures=1,
            window_started_at=now,
            updated_at=now,
        )
        db.add(throttle)
    elif _aware(throttle.window_started_at) + window <= now:
        throttle.failures = 1
        throttle.window_started_at = now
        throttle.blocked_until = None
    else:
        throttle.failures += 1
    if throttle.failures >= settings.login_max_failures:
        throttle.blocked_until = now + window
    db.commit()


def clear_login_failures(db: Session, email: str, client_host: str) -> None:
    throttle = db.get(AuthenticationThrottle, _key(email, client_host))
    if throttle is not None:
        db.delete(throttle)
        db.commit()
