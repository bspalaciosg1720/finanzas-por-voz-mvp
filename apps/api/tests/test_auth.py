from app.modules.auth.models import RefreshSession
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

REGISTER_PAYLOAD = {
    "email": "ana@example.com",
    "password": "correct-horse-battery-staple",
    "full_name": "Ana López",
    "country_code": "CO",
    "timezone": "America/Bogota",
    "default_currency": "COP",
    "device_name": "Test phone",
}


def register(client: TestClient):
    return client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)


def test_register_and_get_profile(client: TestClient) -> None:
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["user"]["email"] == "ana@example.com"
    assert body["tokens"]["token_type"] == "bearer"

    profile = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {body['tokens']['access_token']}"},
    )
    assert profile.status_code == 200
    assert profile.json()["id"] == body["user"]["id"]


def test_duplicate_email_is_rejected(client: TestClient) -> None:
    assert register(client).status_code == 201
    response = register(client)
    assert response.status_code == 409
    assert response.headers["content-type"].startswith("application/problem+json")


def test_login_rejects_wrong_password(client: TestClient) -> None:
    assert register(client).status_code == 201
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "ana@example.com",
            "password": "incorrect-password",
            "device_name": "Test phone",
        },
    )
    assert response.status_code == 401


def test_refresh_rotates_and_rejects_reuse(client: TestClient) -> None:
    initial = register(client).json()["tokens"]
    rotated = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial["refresh_token"]},
    )
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != initial["refresh_token"]

    reuse = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": initial["refresh_token"]},
    )
    assert reuse.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    tokens = register(client).json()["tokens"]
    logout = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout.status_code == 204

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 401


def test_profile_requires_access_token(client: TestClient) -> None:
    assert client.get("/api/v1/me").status_code == 401


def test_refresh_token_is_not_stored_in_plaintext(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    refresh_token = register(client).json()["tokens"]["refresh_token"]
    with db_factory() as db:
        stored = db.scalar(select(RefreshSession))
    assert stored is not None
    assert stored.token_hash != refresh_token
    assert len(stored.token_hash) == 64


def test_user_can_list_and_revoke_own_session(client: TestClient) -> None:
    auth = register(client).json()
    headers = {"Authorization": f"Bearer {auth['tokens']['access_token']}"}

    sessions = client.get("/api/v1/auth/sessions", headers=headers)
    assert sessions.status_code == 200
    assert len(sessions.json()) == 1
    assert sessions.json()[0]["device_name"] == "Test phone"

    session_id = sessions.json()[0]["id"]
    revoked = client.delete(f"/api/v1/auth/sessions/{session_id}", headers=headers)
    assert revoked.status_code == 204

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": auth["tokens"]["refresh_token"]},
    )
    assert refresh.status_code == 401


def test_user_cannot_revoke_another_users_session(client: TestClient) -> None:
    first = register(client).json()
    second_payload = {
        **REGISTER_PAYLOAD,
        "email": "beatriz@example.com",
        "full_name": "Beatriz Ruiz",
    }
    second = client.post("/api/v1/auth/register", json=second_payload).json()

    second_sessions = client.get(
        "/api/v1/auth/sessions",
        headers={"Authorization": f"Bearer {second['tokens']['access_token']}"},
    ).json()

    attempt = client.delete(
        f"/api/v1/auth/sessions/{second_sessions[0]['id']}",
        headers={"Authorization": f"Bearer {first['tokens']['access_token']}"},
    )
    assert attempt.status_code == 404

    still_valid = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": second["tokens"]["refresh_token"]},
    )
    assert still_valid.status_code == 200
