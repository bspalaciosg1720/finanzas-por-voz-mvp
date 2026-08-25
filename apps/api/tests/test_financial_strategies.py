from datetime import UTC, datetime


def auth_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "estrategias@example.com",
            "password": "Clave-segura-2026",
            "full_name": "Ana Estrategias",
            "country_code": "CO",
            "timezone": "America/Bogota",
            "default_currency": "COP",
        },
    )
    return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}


def test_strategy_config_and_analysis_are_adaptive(client):
    headers = auth_headers(client)
    updated = client.patch(
        "/api/v1/financial-strategies/config",
        headers=headers,
        json={
            "zero_based_enabled": True,
            "pay_first_enabled": True,
            "pay_first_percent": 12,
            "extraordinary_debt_percent": 50,
            "extraordinary_savings_percent": 20,
            "extraordinary_goals_percent": 20,
            "extraordinary_personal_percent": 10,
            "no_spend_days_enabled": True,
            "no_spend_weekdays": [1, 3],
            "purchase_wait_enabled": True,
            "purchase_wait_hours": 48,
        },
    )
    assert updated.status_code == 200
    assert updated.json()["pay_first_percent"] == 12
    assert updated.json()["no_spend_weekdays"] == [1, 3]

    response = client.get("/api/v1/financial-strategies/analysis", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["financial_level"] == "protect"
    assert body["priority_order"][0] == "basic_needs"
    strategies = {item["key"]: item for item in body["strategies"]}
    assert len(strategies) == 14
    assert strategies["zero_based"]["enabled"] is True
    assert strategies["pay_first"]["impact_minor"] == 0
    assert strategies["automatic_priorities"]["recommended"] is True


def test_sinking_fund_keeps_monthly_plan(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/v1/savings-goals",
        headers=headers,
        json={
            "name": "Seguro anual",
            "goal_type": "sinking_fund",
            "target_amount_minor": 1_200_000,
            "planned_monthly_minor": 100_000,
            "currency": "COP",
        },
    )
    assert created.status_code == 201
    goal = client.get("/api/v1/savings-goals", headers=headers).json()[0]
    assert goal["goal_type"] == "sinking_fund"
    assert goal["planned_monthly_minor"] == 100_000


def test_pay_first_automates_once_for_an_idempotent_income(client):
    headers = auth_headers(client)
    goal_id = client.post(
        "/api/v1/savings-goals",
        headers=headers,
        json={
            "name": "Reserva automática",
            "target_amount_minor": 2_000_000,
            "currency": "COP",
        },
    ).json()["id"]
    configured = client.patch(
        "/api/v1/financial-strategies/config",
        headers=headers,
        json={
            "pay_first_enabled": True,
            "pay_first_percent": 10,
            "pay_first_goal_id": goal_id,
        },
    )
    assert configured.status_code == 200
    income_headers = {
        **headers,
        "Idempotency-Key": "88888888-8888-4888-8888-888888888888",
    }
    payload = {
        "type": "income",
        "amount_minor": 1_000_000,
        "currency": "COP",
        "category_id": None,
        "description": "Ingreso",
        "occurred_at": datetime.now(UTC).isoformat(),
        "source": "manual",
    }
    assert (
        client.post("/api/v1/transactions", headers=income_headers, json=payload).status_code == 201
    )
    assert (
        client.post("/api/v1/transactions", headers=income_headers, json=payload).status_code == 201
    )
    goal = client.get("/api/v1/savings-goals", headers=headers).json()[0]
    assert goal["saved_amount_minor"] == 100_000
    assert len(goal["contributions"]) == 1
