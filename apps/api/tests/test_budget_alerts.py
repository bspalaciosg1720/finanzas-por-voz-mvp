import uuid

from app.modules.budgets.models import BudgetAlert
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker
from tests.test_budgets import add_budget, seed_expense_category
from tests.test_transactions import auth_headers, create, payload, register


def expense(category_id: uuid.UUID, amount: int) -> dict:
    return {
        **payload(
            amount=amount,
            occurred_at="2026-07-15T12:00:00-05:00",
        ),
        "category_id": str(category_id),
    }


def test_alerts_are_deduplicated_by_budget_period_and_level(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "budget-alerts@example.com")
    category = seed_expense_category(db_factory)
    add_budget(client, auth, category.id, amount=100_000)

    key = uuid.uuid4()
    assert create(client, auth, expense(category.id, 80_000), key=key).status_code == 201
    assert create(client, auth, expense(category.id, 80_000), key=key).status_code == 201
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(BudgetAlert)) == 1

    create(client, auth, expense(category.id, 5_000))
    with db_factory() as db:
        assert db.scalar(select(func.count()).select_from(BudgetAlert)) == 1

    create(client, auth, expense(category.id, 15_000))
    alerts = client.get(
        "/api/v1/budgets/alerts",
        headers=auth_headers(auth),
    ).json()
    assert {alert["level"] for alert in alerts} == {"warning", "exceeded"}


def test_alerts_can_be_read_and_are_isolated(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    owner = register(client, "budget-alert-owner@example.com")
    other = register(client, "budget-alert-other@example.com")
    category = seed_expense_category(db_factory, name="Transporte")
    add_budget(client, owner, category.id, amount=50_000)
    create(client, owner, expense(category.id, 50_000))

    alerts = client.get(
        "/api/v1/budgets/alerts",
        headers=auth_headers(owner),
    ).json()
    assert len(alerts) == 1
    alert_id = alerts[0]["id"]
    assert (
        client.patch(
            f"/api/v1/budgets/alerts/{alert_id}/read",
            headers=auth_headers(other),
        ).status_code
        == 404
    )
    assert (
        client.patch(
            f"/api/v1/budgets/alerts/{alert_id}/read",
            headers=auth_headers(owner),
        ).status_code
        == 204
    )
    assert (
        client.get(
            "/api/v1/budgets/alerts",
            headers=auth_headers(owner),
        ).json()
        == []
    )
    all_alerts = client.get(
        "/api/v1/budgets/alerts?unread_only=false",
        headers=auth_headers(owner),
    ).json()
    assert all_alerts[0]["read_at"] is not None
