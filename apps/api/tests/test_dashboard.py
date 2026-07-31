from fastapi.testclient import TestClient
from tests.test_transactions import auth_headers, create, payload, register


def test_dashboard_calculates_balance_period_comparison_and_recent(
    client: TestClient,
) -> None:
    auth = register(client, "dashboard@example.com")
    create(
        client,
        auth,
        payload(
            amount=1_000_000,
            description="Salario",
            occurred_at="2026-07-02T08:00:00-05:00",
            movement_type="income",
        ),
    )
    create(
        client,
        auth,
        payload(
            amount=200_000,
            description="Mercado",
            occurred_at="2026-07-10T12:00:00-05:00",
        ),
    )
    create(
        client,
        auth,
        payload(
            amount=100_000,
            description="Gasto anterior",
            occurred_at="2026-06-10T12:00:00-05:00",
        ),
    )

    response = client.get(
        "/api/v1/dashboard/summary?year=2026&month=7",
        headers=auth_headers(auth),
    )
    assert response.status_code == 200
    summary = response.json()
    assert summary["balance_minor"] == 700_000
    assert summary["income_minor"] == 1_000_000
    assert summary["expense_minor"] == 200_000
    assert summary["previous_expense_minor"] == 100_000
    assert summary["expense_change_percent"] == 100.0
    assert summary["top_expense_category"]["name"] == "Sin categoría"
    assert [item["description"] for item in summary["recent_transactions"]] == [
        "Mercado",
        "Salario",
        "Gasto anterior",
    ]


def test_dashboard_is_isolated_and_ignores_deleted_transactions(
    client: TestClient,
) -> None:
    owner = register(client, "dashboard-owner@example.com")
    other = register(client, "dashboard-other@example.com")
    transaction = create(
        client,
        owner,
        payload(
            amount=500_000,
            occurred_at="2026-07-15T12:00:00-05:00",
            movement_type="income",
        ),
    ).json()
    client.delete(
        f"/api/v1/transactions/{transaction['id']}",
        headers=auth_headers(owner),
    )
    create(
        client,
        other,
        payload(
            amount=900_000,
            occurred_at="2026-07-15T12:00:00-05:00",
            movement_type="income",
        ),
    )

    summary = client.get(
        "/api/v1/dashboard/summary?year=2026&month=7",
        headers=auth_headers(owner),
    ).json()
    assert summary["balance_minor"] == 0
    assert summary["income_minor"] == 0
    assert summary["recent_transactions"] == []
