import uuid
from datetime import UTC, timedelta

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import (
    create_access_token,
    create_refresh_secret,
    hash_password,
    hash_refresh_secret,
    verify_password,
)
from app.infrastructure.email import EmailMessage, EmailSender
from app.modules.auth.action_tokens import consume_action_token, create_action_token
from app.modules.auth.models import AuthIdentity, RefreshSession
from app.modules.auth.schemas import (
    AuthResponse,
    LoginRequest,
    RegisterRequest,
    TokenPair,
    UserResponse,
)
from app.modules.users.models import User
from app.shared.time import utc_now


def issue_session(db: Session, user: User, device_name: str) -> TokenPair:
    settings = get_settings()
    refresh_secret = create_refresh_secret()
    session = RefreshSession(
        user_id=user.id,
        token_hash=hash_refresh_secret(refresh_secret),
        device_name=device_name,
        expires_at=utc_now() + timedelta(days=settings.refresh_token_days),
    )
    db.add(session)
    db.flush()
    access_token, expires_in = create_access_token(user.id)
    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_secret,
        expires_in=expires_in,
    )


def register(db: Session, payload: RegisterRequest) -> AuthResponse:
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        country_code=payload.country_code,
        timezone=payload.timezone,
        default_currency=payload.default_currency,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    try:
        db.flush()
        db.add(
            AuthIdentity(
                user_id=user.id,
                provider="password",
                provider_subject=user.email,
            )
        )
        tokens = issue_session(db, user, payload.device_name)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise AppError(
            status=409,
            title="Email already registered",
            detail="An account already exists for this email.",
            error_type="email-conflict",
        ) from exc
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


def login(db: Session, payload: LoginRequest) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if (
        user is None
        or user.password_hash is None
        or not verify_password(payload.password, user.password_hash)
    ):
        raise AppError(
            status=401,
            title="Invalid credentials",
            detail="Email or password is incorrect.",
            error_type="invalid-credentials",
        )
    if user.status != "active":
        raise AppError(
            status=403,
            title="Account unavailable",
            detail="This account cannot start a session.",
            error_type="account-unavailable",
        )
    tokens = issue_session(db, user, payload.device_name)
    db.commit()
    return AuthResponse(user=UserResponse.model_validate(user), tokens=tokens)


def rotate_refresh_token(db: Session, refresh_secret: str) -> TokenPair:
    now = utc_now()
    session = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == hash_refresh_secret(refresh_secret)
        )
    )
    expires_at = session.expires_at if session is not None else None
    if expires_at is not None and expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    if session is None or session.revoked_at is not None or expires_at is None or expires_at <= now:
        raise AppError(
            status=401,
            title="Invalid session",
            detail="Refresh token is invalid or expired.",
            error_type="invalid-refresh-token",
        )

    user = db.get(User, session.user_id)
    if user is None or user.status != "active":
        raise AppError(
            status=401,
            title="Invalid session",
            detail="The account for this session is unavailable.",
            error_type="invalid-refresh-token",
        )

    session.revoked_at = now
    session.last_used_at = now
    tokens = issue_session(db, user, session.device_name)
    db.commit()
    return tokens


def revoke_refresh_token(db: Session, refresh_secret: str) -> None:
    session = db.scalar(
        select(RefreshSession).where(
            RefreshSession.token_hash == hash_refresh_secret(refresh_secret)
        )
    )
    if session is not None and session.revoked_at is None:
        session.revoked_at = utc_now()
        db.commit()


def list_user_sessions(db: Session, user: User) -> list[RefreshSession]:
    return list(
        db.scalars(
            select(RefreshSession)
            .where(RefreshSession.user_id == user.id)
            .order_by(RefreshSession.created_at.desc())
        )
    )


def revoke_user_session(db: Session, user: User, session_id: uuid.UUID) -> None:
    session = db.scalar(
        select(RefreshSession).where(
            RefreshSession.id == session_id,
            RefreshSession.user_id == user.id,
        )
    )
    if session is None:
        raise AppError(
            status=404,
            title="Session not found",
            detail="The requested session does not exist.",
            error_type="session-not-found",
        )
    if session.revoked_at is None:
        session.revoked_at = utc_now()
        db.commit()


def request_email_verification(db: Session, user: User, sender: EmailSender) -> None:
    if user.email_verified_at is not None:
        return
    secret = create_action_token(
        db,
        user_id=user.id,
        purpose="verify_email",
        lifetime=timedelta(hours=24),
    )
    db.commit()
    url = f"{str(get_settings().public_app_url).rstrip('/')}/verify-email?token={secret}"
    sender.send(
        EmailMessage(
            recipient=user.email,
            subject="Verifica tu correo",
            text=f"Abre este enlace para verificar tu cuenta:\n{url}\n\nExpira en 24 horas.",
        )
    )


def verify_email(db: Session, secret: str) -> None:
    action = consume_action_token(db, secret=secret, purpose="verify_email")
    user = db.get(User, action.user_id)
    if user is None:
        raise AppError(
            status=400,
            title="Invalid or expired token",
            detail="Request a new link and try again.",
            error_type="invalid-action-token",
        )
    user.email_verified_at = utc_now()
    db.commit()


def request_password_reset(db: Session, email: str, sender: EmailSender) -> None:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or user.status != "active":
        return
    secret = create_action_token(
        db,
        user_id=user.id,
        purpose="reset_password",
        lifetime=timedelta(minutes=30),
    )
    db.commit()
    url = f"{str(get_settings().public_app_url).rstrip('/')}/reset-password?token={secret}"
    sender.send(
        EmailMessage(
            recipient=user.email,
            subject="Restablece tu contraseña",
            text=f"Abre este enlace para cambiar tu contraseña:\n{url}\n\nExpira en 30 minutos.",
        )
    )


def reset_password(db: Session, secret: str, new_password: str) -> None:
    action = consume_action_token(db, secret=secret, purpose="reset_password")
    user = db.get(User, action.user_id)
    if user is None or user.status != "active":
        raise AppError(
            status=400,
            title="Invalid or expired token",
            detail="Request a new link and try again.",
            error_type="invalid-action-token",
        )
    now = utc_now()
    user.password_hash = hash_password(new_password)
    db.execute(
        update(RefreshSession)
        .where(
            RefreshSession.user_id == user.id,
            RefreshSession.revoked_at.is_(None),
        )
        .values(revoked_at=now)
    )
    db.commit()
