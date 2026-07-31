import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.infrastructure.database import get_db
from app.infrastructure.email import EmailSender, get_email_sender
from app.modules.auth.dependencies import CurrentUser
from app.modules.auth.schemas import (
    ActionTokenRequest,
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionResponse,
    TokenPair,
    UserResponse,
)
from app.modules.auth.service import (
    list_user_sessions,
    login,
    register,
    request_email_verification,
    request_password_reset,
    reset_password,
    revoke_refresh_token,
    revoke_user_session,
    rotate_refresh_token,
    verify_email,
)

router = APIRouter(prefix="/auth", tags=["Auth"])
profile_router = APIRouter(tags=["Users"])
DbSession = Annotated[Session, Depends(get_db)]
EmailSenderDependency = Annotated[EmailSender, Depends(get_email_sender)]


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register_user(payload: RegisterRequest, db: DbSession) -> AuthResponse:
    return register(db, payload)


@router.post("/login", response_model=AuthResponse)
def login_user(payload: LoginRequest, db: DbSession) -> AuthResponse:
    return login(db, payload)


@router.post("/refresh", response_model=TokenPair)
def refresh_session(payload: RefreshRequest, db: DbSession) -> TokenPair:
    return rotate_refresh_token(db, payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout_user(payload: LogoutRequest, db: DbSession) -> Response:
    revoke_refresh_token(db, payload.refresh_token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sessions", response_model=list[SessionResponse])
def get_sessions(user: CurrentUser, db: DbSession) -> list[SessionResponse]:
    return [SessionResponse.model_validate(session) for session in list_user_sessions(db, user)]


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id: uuid.UUID, user: CurrentUser, db: DbSession) -> Response:
    revoke_user_session(db, user, session_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email/request", status_code=status.HTTP_202_ACCEPTED)
def send_verification_email(
    user: CurrentUser,
    db: DbSession,
    sender: EmailSenderDependency,
) -> Response:
    request_email_verification(db, user, sender)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/verify-email/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_email(payload: ActionTokenRequest, db: DbSession) -> Response:
    verify_email(db, payload.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/password/forgot", status_code=status.HTTP_202_ACCEPTED)
def forgot_password(
    payload: ForgotPasswordRequest,
    db: DbSession,
    sender: EmailSenderDependency,
) -> Response:
    request_password_reset(db, payload.email, sender)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/password/reset", status_code=status.HTTP_204_NO_CONTENT)
def change_password(payload: ResetPasswordRequest, db: DbSession) -> Response:
    reset_password(db, payload.token, payload.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@profile_router.get("/me", response_model=UserResponse)
def get_profile(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)
