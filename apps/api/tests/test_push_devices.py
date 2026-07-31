import asyncio

from app.modules.notifications.delivery import FakePushSender, PushMessage
from fastapi.testclient import TestClient
from tests.test_transactions import auth_headers, register

TOKEN = "ExpoPushToken[abcdefghijklmnopqrstuvwxyz123456]"


def add_device(client: TestClient, auth: dict, token: str = TOKEN):
    return client.post(
        "/api/v1/push-devices",
        headers=auth_headers(auth),
        json={
            "token": token,
            "platform": "android",
            "device_name": "Pixel de prueba",
        },
    )


def test_push_device_registration_is_idempotent_and_hides_token(
    client: TestClient,
) -> None:
    auth = register(client, "push-device@example.com")
    first = add_device(client, auth)
    repeated = add_device(client, auth)
    assert first.status_code == 201
    assert repeated.status_code == 201
    assert repeated.json()["id"] == first.json()["id"]
    assert "token" not in repeated.json()

    listed = client.get(
        "/api/v1/push-devices",
        headers=auth_headers(auth),
    ).json()
    assert len(listed) == 1
    assert "token" not in listed[0]


def test_push_device_validation_revocation_and_isolation(client: TestClient) -> None:
    owner = register(client, "push-owner@example.com")
    other = register(client, "push-other@example.com")
    assert add_device(client, owner, "invalid-token").status_code == 422
    device_id = add_device(client, owner).json()["id"]

    assert (
        client.delete(
            f"/api/v1/push-devices/{device_id}",
            headers=auth_headers(other),
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/api/v1/push-devices/{device_id}",
            headers=auth_headers(owner),
        ).status_code
        == 204
    )
    assert (
        client.get("/api/v1/push-devices", headers=auth_headers(owner)).json()
        == []
    )


def test_fake_push_sender_records_without_external_delivery() -> None:
    sender = FakePushSender()
    message = PushMessage(
        token=TOKEN,
        title="Cerca del límite",
        body="Revisa tu presupuesto.",
        data={"type": "budget_warning"},
    )
    asyncio.run(sender.send(message))
    assert sender.sent == [message]
