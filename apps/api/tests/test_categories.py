import uuid

from app.modules.categories.models import Category
from fastapi.testclient import TestClient
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


def test_categories_include_system_and_only_current_user_custom_categories(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    first = register(client, "first@example.com")
    second = register(client, "second@example.com")

    with db_factory.begin() as db:
        db.add_all(
            [
                Category(
                    id=uuid.uuid4(),
                    name="Alimentación",
                    slug="alimentacion",
                    icon="food",
                    movement_scope="expense",
                    is_system=True,
                    is_active=True,
                ),
                Category(
                    id=uuid.uuid4(),
                    user_id=uuid.UUID(first["user"]["id"]),
                    name="Café",
                    slug="cafe",
                    icon="coffee",
                    movement_scope="expense",
                    is_system=False,
                    is_active=True,
                ),
            ]
        )

    first_response = client.get(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {first['tokens']['access_token']}"},
    )
    second_response = client.get(
        "/api/v1/categories",
        headers={"Authorization": f"Bearer {second['tokens']['access_token']}"},
    )

    assert first_response.status_code == 200
    assert {item["name"] for item in first_response.json()} == {"Alimentación", "Café"}
    assert second_response.status_code == 200
    assert {item["name"] for item in second_response.json()} == {"Alimentación"}


def test_custom_category_crud_and_conflict(client: TestClient) -> None:
    auth = register(client, "owner@example.com")
    headers = {"Authorization": f"Bearer {auth['tokens']['access_token']}"}

    created = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Café diario", "icon": "coffee", "movement_scope": "expense"},
    )
    assert created.status_code == 201
    category_id = created.json()["id"]
    assert created.json()["slug"] == "cafe-diario"

    duplicate = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Café diario", "icon": "coffee", "movement_scope": "expense"},
    )
    assert duplicate.status_code == 409

    updated = client.patch(
        f"/api/v1/categories/{category_id}",
        headers=headers,
        json={"name": "Café y pan"},
    )
    assert updated.status_code == 200
    assert updated.json()["slug"] == "cafe-y-pan"

    deleted = client.delete(f"/api/v1/categories/{category_id}", headers=headers)
    assert deleted.status_code == 204

    listed = client.get("/api/v1/categories", headers=headers)
    assert "Café y pan" not in {item["name"] for item in listed.json()}


def test_user_cannot_modify_another_users_category(client: TestClient) -> None:
    first = register(client, "first-owner@example.com")
    second = register(client, "second-owner@example.com")
    first_headers = {"Authorization": f"Bearer {first['tokens']['access_token']}"}
    second_headers = {"Authorization": f"Bearer {second['tokens']['access_token']}"}

    category_id = client.post(
        "/api/v1/categories",
        headers=first_headers,
        json={"name": "Personal", "icon": "star", "movement_scope": "expense"},
    ).json()["id"]

    attempt = client.patch(
        f"/api/v1/categories/{category_id}",
        headers=second_headers,
        json={"name": "Modificada"},
    )
    assert attempt.status_code == 404
