from fastapi.testclient import TestClient


def register(client: TestClient, email: str = "correo@example.com") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "correct-horse-battery-staple",
            "full_name": "Test User",
            "country_code": "CO",
            "timezone": "America/Bogota",
            "default_currency": "COP",
            "device_name": "Test phone",
        },
    )
    assert response.status_code == 201
    return response.json()


def auth_headers(auth: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {auth['tokens']['access_token']}"}


def inbound_payload(recipient: str, message_id: str = "bank-001") -> dict:
    return {
        "recipient": recipient,
        "sender": "Alertas Banco <alertas@banco.example>",
        "subject": "Compra aprobada",
        "text": "Realizaste una compra por $42.900 en EXITO el día de hoy.",
        "message_id": message_id,
        "received_at": "2026-08-03T10:15:00-05:00",
    }


def test_inbound_email_creates_deduplicated_suggestion(client: TestClient) -> None:
    auth = register(client)
    headers = auth_headers(auth)
    inbox = client.get("/api/v1/transaction-suggestions/inbox", headers=headers)
    assert inbox.status_code == 200
    address = inbox.json()["address"]
    assert address.startswith("movimientos+")

    webhook_headers = {
        "X-Inbound-Email-Secret": "development-inbound-email-secret-change-me"
    }
    first = client.post(
        "/api/v1/transaction-suggestions/inbound-email",
        headers=webhook_headers,
        json=inbound_payload(address),
    )
    repeated = client.post(
        "/api/v1/transaction-suggestions/inbound-email",
        headers=webhook_headers,
        json=inbound_payload(address),
    )
    assert first.status_code == 200
    assert repeated.status_code == 200
    assert first.json()["id"] == repeated.json()["id"]
    assert first.json()["amount_minor"] == 42_900
    assert first.json()["type"] == "expense"
    assert first.json()["description"] == "EXITO"

    pending = client.get("/api/v1/transaction-suggestions", headers=headers)
    assert pending.status_code == 200
    assert len(pending.json()) == 1


def test_confirm_creates_transaction_once(client: TestClient) -> None:
    auth = register(client, "confirm@example.com")
    headers = auth_headers(auth)
    address = client.get(
        "/api/v1/transaction-suggestions/inbox", headers=headers
    ).json()["address"]
    suggestion = client.post(
        "/api/v1/transaction-suggestions/inbound-email",
        headers={
            "X-Inbound-Email-Secret": "development-inbound-email-secret-change-me"
        },
        json=inbound_payload(address, "confirm-001"),
    ).json()

    first = client.post(
        f"/api/v1/transaction-suggestions/{suggestion['id']}/confirm",
        headers=headers,
        json={"description": "Mercado semanal"},
    )
    repeated = client.post(
        f"/api/v1/transaction-suggestions/{suggestion['id']}/confirm",
        headers=headers,
        json={},
    )
    assert first.status_code == 200
    assert repeated.status_code == 200
    assert first.json()["transaction_id"] == repeated.json()["transaction_id"]

    transactions = client.get("/api/v1/transactions", headers=headers).json()["items"]
    assert len(transactions) == 1
    assert transactions[0]["description"] == "Mercado semanal"
    assert transactions[0]["source"] == "integration"


def test_webhook_and_suggestions_are_protected(client: TestClient) -> None:
    auth = register(client, "owner@example.com")
    address = client.get(
        "/api/v1/transaction-suggestions/inbox", headers=auth_headers(auth)
    ).json()["address"]
    rejected = client.post(
        "/api/v1/transaction-suggestions/inbound-email",
        headers={"X-Inbound-Email-Secret": "x" * 40},
        json=inbound_payload(address),
    )
    assert rejected.status_code == 401

    other = register(client, "other@example.com")
    missing = client.post(
        "/api/v1/transaction-suggestions/00000000-0000-0000-0000-000000000001/discard",
        headers=auth_headers(other),
    )
    assert missing.status_code == 404
