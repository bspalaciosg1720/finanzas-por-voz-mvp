import uuid

from app.modules.categories.models import Category
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.test_transactions import auth_headers, create, payload, register


def seed_expense_category(
    db_factory: sessionmaker[Session],
    *,
    name: str = "Alimentación",
) -> Category:
    with db_factory() as db:
        category = Category(
            id=uuid.uuid4(),
            user_id=None,
            name=name,
            slug=name.lower(),
            icon="test",
            movement_scope="expense",
            is_system=True,
            is_active=True,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category


def add_budget(
    client: TestClient,
    auth: dict,
    category_id: uuid.UUID,
    *,
    amount: int = 100_000,
):
    return client.post(
        "/api/v1/budgets",
        headers=auth_headers(auth),
        json={
            "category_id": str(category_id),
            "amount_minor": amount,
            "currency": "COP",
            "alert_threshold_percent": 80,
        },
    )


def test_budget_progress_warning_and_exceeded(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "budget-progress@example.com")
    category = seed_expense_category(db_factory)
    assert add_budget(client, auth, category.id).status_code == 201

    transaction = {
        **payload(
            amount=80_000,
            occurred_at="2026-07-15T12:00:00-05:00",
        ),
        "category_id": str(category.id),
    }
    assert create(client, auth, transaction).status_code == 201

    response = client.get(
        "/api/v1/budgets?reference_at=2026-07-30T12:00:00-05:00",
        headers=auth_headers(auth),
    )
    assert response.status_code == 200
    budget = response.json()[0]
    assert budget["spent_minor"] == 80_000
    assert budget["progress_percent"] == 80.0
    assert budget["alert_status"] == "warning"

    create(
        client,
        auth,
        {
            **payload(
                amount=25_000,
                occurred_at="2026-07-20T12:00:00-05:00",
            ),
            "category_id": str(category.id),
        },
    )
    exceeded = client.get(
        "/api/v1/budgets?reference_at=2026-07-30T12:00:00-05:00",
        headers=auth_headers(auth),
    ).json()[0]
    assert exceeded["spent_minor"] == 105_000
    assert exceeded["alert_status"] == "exceeded"


def test_budget_excludes_other_months_income_and_deleted_transactions(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "budget-exclusions@example.com")
    category = seed_expense_category(db_factory, name="Transporte")
    add_budget(client, auth, category.id)
    values = [
        payload(amount=30_000, occurred_at="2026-06-30T12:00:00-05:00"),
        payload(
            amount=40_000,
            occurred_at="2026-07-05T12:00:00-05:00",
            movement_type="income",
        ),
        payload(amount=50_000, occurred_at="2026-07-10T12:00:00-05:00"),
    ]
    ids = []
    for value in values:
        result = create(
            client,
            auth,
            {**value, "category_id": str(category.id)},
        )
        ids.append(result.json()["id"])
    client.delete(
        f"/api/v1/transactions/{ids[-1]}",
        headers=auth_headers(auth),
    )

    budget = client.get(
        "/api/v1/budgets?reference_at=2026-07-30T12:00:00-05:00",
        headers=auth_headers(auth),
    ).json()[0]
    assert budget["spent_minor"] == 0
    assert budget["alert_status"] == "on_track"


def test_budget_crud_conflict_validation_and_user_isolation(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    owner = register(client, "budget-owner@example.com")
    other = register(client, "budget-other@example.com")
    category = seed_expense_category(db_factory, name="Salud")
    created = add_budget(client, owner, category.id)
    budget_id = created.json()["id"]

    assert add_budget(client, owner, category.id).status_code == 409
    assert add_budget(client, owner, category.id, amount=0).status_code == 422
    assert (
        client.patch(
            f"/api/v1/budgets/{budget_id}",
            headers=auth_headers(other),
            json={"amount_minor": 200_000},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/budgets/{budget_id}",
            headers=auth_headers(owner),
            json={"amount_minor": 200_000, "alert_threshold_percent": 75},
        ).status_code
        == 204
    )
    assert (
        client.delete(
            f"/api/v1/budgets/{budget_id}",
            headers=auth_headers(owner),
        ).status_code
        == 204
    )
    assert client.get("/api/v1/budgets", headers=auth_headers(owner)).json() == []
