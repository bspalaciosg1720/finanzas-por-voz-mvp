import uuid

from app.modules.transactions.models import Transaction
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker


def register(client: TestClient, email: str) -> dict:
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


def payload(
    *,
    amount: int = 18_000,
    description: str = "Almuerzo",
    occurred_at: str = "2026-07-30T12:40:00-05:00",
    movement_type: str = "expense",
) -> dict:
    return {
        "type": movement_type,
        "amount_minor": amount,
        "currency": "COP",
        "category_id": None,
        "description": description,
        "occurred_at": occurred_at,
        "source": "manual",
    }


def auth_headers(auth: dict, key: uuid.UUID | None = None) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {auth['tokens']['access_token']}"}
    if key:
        headers["Idempotency-Key"] = str(key)
    return headers


def create(client: TestClient, auth: dict, data: dict | None = None, key=None):
    return client.post(
        "/api/v1/transactions",
        headers=auth_headers(auth, key or uuid.uuid4()),
        json=data or payload(),
    )


def test_create_requires_integer_positive_amount_and_timezone(client: TestClient) -> None:
    auth = register(client, "amount@example.com")
    assert create(client, auth, payload(amount=0)).status_code == 422
    assert create(client, auth, {**payload(), "amount_minor": 18.5}).status_code == 422
    assert (
        create(
            client,
            auth,
            {**payload(), "occurred_at": "2026-07-30T12:40:00"},
        ).status_code
        == 422
    )


def test_idempotency_prevents_duplicates_and_payload_reuse(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "idempotency@example.com")
    key = uuid.uuid4()
    first = create(client, auth, key=key)
    repeated = create(client, auth, key=key)
    conflict = create(client, auth, payload(amount=20_000), key=key)

    assert first.status_code == 201
    assert repeated.status_code == 201
    assert repeated.json()["id"] == first.json()["id"]
    assert conflict.status_code == 409
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(Transaction)) == 1


def test_user_cannot_access_or_mutate_another_users_transaction(client: TestClient) -> None:
    owner = register(client, "owner-transaction@example.com")
    other = register(client, "other-transaction@example.com")
    transaction_id = create(client, owner).json()["id"]

    assert (
        client.get(
            f"/api/v1/transactions/{transaction_id}",
            headers=auth_headers(other),
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/transactions/{transaction_id}",
            headers=auth_headers(other),
            json={"amount_minor": 1},
        ).status_code
        == 404
    )


def test_edit_delete_and_restore(client: TestClient) -> None:
    auth = register(client, "lifecycle@example.com")
    transaction_id = create(client, auth).json()["id"]

    edited = client.patch(
        f"/api/v1/transactions/{transaction_id}",
        headers=auth_headers(auth),
        json={"amount_minor": 22_000, "description": "Almuerzo ejecutivo"},
    )
    assert edited.status_code == 200
    assert edited.json()["amount_minor"] == 22_000

    deleted = client.delete(
        f"/api/v1/transactions/{transaction_id}",
        headers=auth_headers(auth),
    )
    assert deleted.status_code == 204
    assert client.get("/api/v1/transactions", headers=auth_headers(auth)).json()["items"] == []

    restored = client.post(
        f"/api/v1/transactions/{transaction_id}/restore",
        headers=auth_headers(auth),
    )
    assert restored.status_code == 200
    assert restored.json()["status"] == "confirmed"


def test_filters_search_and_stable_cursor_pagination(client: TestClient) -> None:
    auth = register(client, "filters@example.com")
    create(
        client,
        auth,
        payload(description="Almuerzo", occurred_at="2026-07-30T12:00:00-05:00"),
    )
    create(
        client,
        auth,
        payload(
            amount=1_000_000,
            description="Salario",
            occurred_at="2026-07-29T09:00:00-05:00",
            movement_type="income",
        ),
    )
    create(
        client,
        auth,
        payload(description="Taxi", occurred_at="2026-07-28T18:00:00-05:00"),
    )

    first_page = client.get(
        "/api/v1/transactions?limit=2",
        headers=auth_headers(auth),
    ).json()
    assert [item["description"] for item in first_page["items"]] == [
        "Almuerzo",
        "Salario",
    ]
    assert first_page["next_cursor"]

    second_page = client.get(
        f"/api/v1/transactions?limit=2&cursor={first_page['next_cursor']}",
        headers=auth_headers(auth),
    ).json()
    assert [item["description"] for item in second_page["items"]] == ["Taxi"]

    incomes = client.get(
        "/api/v1/transactions?type=income",
        headers=auth_headers(auth),
    ).json()
    assert [item["description"] for item in incomes["items"]] == ["Salario"]

    search = client.get(
        "/api/v1/transactions?query=tax",
        headers=auth_headers(auth),
    ).json()
    assert [item["description"] for item in search["items"]] == ["Taxi"]

    date_filter = client.get(
        "/api/v1/transactions?from=2026-07-29&to=2026-07-29",
        headers=auth_headers(auth),
    ).json()
    assert [item["description"] for item in date_filter["items"]] == ["Salario"]


def test_invalid_category_and_cursor_are_rejected(client: TestClient) -> None:
    auth = register(client, "invalid@example.com")
    invalid_category = create(
        client,
        auth,
        {**payload(), "category_id": str(uuid.uuid4())},
    )
    assert invalid_category.status_code == 422

    invalid_cursor = client.get(
        "/api/v1/transactions?cursor=not-valid",
        headers=auth_headers(auth),
    )
    assert invalid_cursor.status_code == 422
