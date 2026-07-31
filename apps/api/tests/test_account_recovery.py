import re
from datetime import timedelta
from urllib.parse import parse_qs, urlparse

from app.infrastructure.email import EmailMessage
from app.modules.auth.models import AccountActionToken
from app.modules.users.models import User
from app.shared.time import utc_now
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

REGISTER = {
    "email": "ana@example.com",
    "password": "original-password-123",
    "full_name": "Ana López",
    "country_code": "CO",
    "timezone": "America/Bogota",
    "default_currency": "COP",
    "device_name": "Test phone",
}


def register(client: TestClient) -> dict:
    response = client.post("/api/v1/auth/register", json=REGISTER)
    assert response.status_code == 201
    return response.json()


def token_from_message(message: EmailMessage) -> str:
    match = re.search(r"https?://\S+", message.text)
    assert match
    return parse_qs(urlparse(match.group()).query)["token"][0]


def test_email_verification_is_single_use(
    client: TestClient,
    mailbox: list[EmailMessage],
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client)
    response = client.post(
        "/api/v1/auth/verify-email/request",
        headers={"Authorization": f"Bearer {auth['tokens']['access_token']}"},
    )
    assert response.status_code == 202, response.text
    assert len(mailbox) == 1
    token = token_from_message(mailbox[0])

    confirmed = client.post(
        "/api/v1/auth/verify-email/confirm",
        json={"token": token},
    )
    assert confirmed.status_code == 204

    reused = client.post(
        "/api/v1/auth/verify-email/confirm",
        json={"token": token},
    )
    assert reused.status_code == 400

    with db_factory() as db:
        user = db.scalar(select(User).where(User.email == REGISTER["email"]))
        assert user is not None
        assert user.email_verified_at is not None


def test_expired_verification_token_is_rejected(
    client: TestClient,
    mailbox: list[EmailMessage],
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client)
    client.post(
        "/api/v1/auth/verify-email/request",
        headers={"Authorization": f"Bearer {auth['tokens']['access_token']}"},
    )
    token = token_from_message(mailbox[0])
    with db_factory.begin() as db:
        action = db.scalar(select(AccountActionToken))
        assert action is not None
        action.expires_at = utc_now() - timedelta(minutes=1)

    response = client.post(
        "/api/v1/auth/verify-email/confirm",
        json={"token": token},
    )
    assert response.status_code == 400


def test_password_reset_revokes_sessions_and_changes_password(
    client: TestClient,
    mailbox: list[EmailMessage],
) -> None:
    auth = register(client)
    forgot = client.post(
        "/api/v1/auth/password/forgot",
        json={"email": REGISTER["email"]},
    )
    assert forgot.status_code == 202
    token = token_from_message(mailbox[0])

    reset = client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "new-secure-password-456"},
    )
    assert reset.status_code == 204

    old_session = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": auth["tokens"]["refresh_token"]},
    )
    assert old_session.status_code == 401

    old_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": REGISTER["email"],
            "password": REGISTER["password"],
            "device_name": "Test phone",
        },
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": REGISTER["email"],
            "password": "new-secure-password-456",
            "device_name": "Test phone",
        },
    )
    assert new_login.status_code == 200

    reused = client.post(
        "/api/v1/auth/password/reset",
        json={"token": token, "new_password": "another-password-789"},
    )
    assert reused.status_code == 400


def test_password_forgot_does_not_reveal_unknown_email(
    client: TestClient,
    mailbox: list[EmailMessage],
) -> None:
    response = client.post(
        "/api/v1/auth/password/forgot",
        json={"email": "unknown@example.com"},
    )
    assert response.status_code == 202
    assert mailbox == []
