from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import decode_access_token
from app.infrastructure.database import get_db
from app.modules.users.models import User

bearer = HTTPBearer(auto_error=False)


def unauthorized() -> AppError:
    return AppError(
        status=401,
        title="Authentication required",
        detail="Provide a valid access token.",
        error_type="unauthorized",
    )


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    if credentials is None:
        raise unauthorized()
    try:
        user_id = decode_access_token(credentials.credentials)
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise unauthorized() from exc
    user = db.get(User, user_id)
    if user is None or user.status != "active":
        raise unauthorized()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
