from datetime import UTC, datetime


def headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "plan@example.com",
            "password": "Clave-segura-2026",
            "full_name": "Ana Plan",
            "country_code": "CO",
            "timezone": "America/Bogota",
            "default_currency": "COP",
        },
    )
    return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}


def test_emergency_fund_withdrawal_tracks_replenishment(client):
    auth = headers(client)
    now = datetime.now(UTC).isoformat()
    deposit = client.post(
        "/api/v1/emergency-fund/events",
        headers={**auth, "Idempotency-Key": "55555555-5555-4555-8555-555555555551"},
        json={
            "event_type": "deposit",
            "amount_minor": 500_000,
            "occurred_at": now,
        },
    )
    assert deposit.status_code == 201
    withdrawal = client.post(
        "/api/v1/emergency-fund/events",
        headers={**auth, "Idempotency-Key": "55555555-5555-4555-8555-555555555552"},
        json={
            "event_type": "withdrawal",
            "amount_minor": 200_000,
            "occurred_at": now,
        },
    )
    assert withdrawal.status_code == 201
    fund = client.get("/api/v1/emergency-fund", headers=auth).json()
    assert fund["balance_minor"] == 300_000
    assert fund["pending_replenishment_minor"] == 200_000
    removed = client.delete(
        f"/api/v1/emergency-fund/events/{withdrawal.json()['id']}", headers=auth
    )
    assert removed.status_code == 204
    corrected = client.get("/api/v1/emergency-fund", headers=auth).json()
    assert corrected["balance_minor"] == 500_000
    assert corrected["pending_replenishment_minor"] == 0


def test_calendar_generates_monthly_due_dates_and_marks_payment(client):
    auth = headers(client)
    category = client.post(
        "/api/v1/categories",
        headers=auth,
        json={"name": "Servicios hogar", "icon": "home", "movement_scope": "expense"},
    ).json()
    created = client.post(
        "/api/v1/financial-calendar/obligations",
        headers=auth,
        json={
            "name": "Internet",
            "obligation_type": "utility",
            "amount_minor": 90_000,
            "currency": "COP",
            "due_day": 28,
            "category_id": category["id"],
        },
    )
    assert created.status_code == 201
    calendar = client.get("/api/v1/financial-calendar?days=45", headers=auth).json()
    item = calendar["items"][0]
    paid = client.post(
        f"/api/v1/financial-calendar/obligations/{created.json()['id']}/payments",
        headers={**auth, "Idempotency-Key": "55555555-5555-4555-8555-555555555553"},
        json={
            "due_date": item["due_date"],
            "paid_at": datetime.now(UTC).isoformat(),
            "amount_minor": 90_000,
        },
    )
    assert paid.status_code == 201
    updated = client.get("/api/v1/financial-calendar?days=45", headers=auth).json()
    assert updated["items"][0]["status"] == "paid"
    assert updated["items"][0]["category_id"] == category["id"]
    movements = client.get("/api/v1/transactions", headers=auth).json()["items"]
    assert movements[0]["category_id"] == category["id"]
    replacement_category = client.post(
        "/api/v1/categories",
        headers=auth,
        json={"name": "Suscripciones", "icon": "repeat", "movement_scope": "expense"},
    ).json()
    changed = client.patch(
        f"/api/v1/financial-calendar/obligations/{created.json()['id']}",
        headers=auth,
        json={"category_id": replacement_category["id"]},
    )
    assert changed.status_code == 200
    historical = client.get("/api/v1/financial-calendar?days=45", headers=auth).json()
    assert historical["items"][0]["category_id"] == category["id"]
    payment_id = updated["items"][0]["payment_id"]
    undone = client.delete(
        f"/api/v1/financial-calendar/obligations/{created.json()['id']}/payments/{payment_id}",
        headers=auth,
    )
    assert undone.status_code == 204
    assert (
        client.get("/api/v1/financial-calendar?days=45", headers=auth).json()["items"][0]["status"]
        == "upcoming"
    )


def test_simulation_is_read_only(client):
    auth = headers(client)
    response = client.post(
        "/api/v1/simulations",
        headers=auth,
        json={
            "scenario": "increase_income",
            "amount_minor": 500_000,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["applied"] is False
    assert (
        body["simulated"]["available_cash_minor"]
        == body["current"]["available_cash_minor"] + 500_000
    )


def test_assistant_uses_rules_when_ai_is_disabled(client):
    auth = headers(client)
    response = client.post(
        "/api/v1/financial-assistant/explain",
        headers=auth,
        json={"question": "¿Cómo voy este mes?"},
    )
    assert response.status_code == 200
    assert response.json()["source"] == "rules"


def test_linked_events_affect_cash_but_not_consumption(client):
    auth = headers(client)
    now = datetime.now(UTC).isoformat()
    income = client.post(
        "/api/v1/transactions",
        headers={
            **auth,
            "Idempotency-Key": "33333333-3333-4333-8333-333333333333",
        },
        json={
            "type": "income",
            "amount_minor": 1_000_000,
            "currency": "COP",
            "category_id": None,
            "description": "Ingreso",
            "occurred_at": now,
            "source": "manual",
        },
    )
    assert income.status_code == 201
    debt = client.post(
        "/api/v1/debts",
        headers=auth,
        json={
            "name": "Tarjeta",
            "debt_type": "credit_card",
            "initial_balance_minor": 500_000,
            "minimum_payment_minor": 50_000,
            "currency": "COP",
            "annual_interest_rate_bps": 2400,
        },
    ).json()
    assert (
        client.post(
            f"/api/v1/debts/{debt['id']}/payments",
            headers={**auth, "Idempotency-Key": "55555555-5555-4555-8555-555555555554"},
            json={
                "amount_minor": 200_000,
                "payment_type": "extra",
                "paid_at": now,
                "note": "",
            },
        ).status_code
        == 201
    )
    assert (
        client.post(
            "/api/v1/emergency-fund/events",
            headers={**auth, "Idempotency-Key": "55555555-5555-4555-8555-555555555555"},
            json={"event_type": "deposit", "amount_minor": 100_000, "occurred_at": now},
        ).status_code
        == 201
    )

    dashboard = client.get("/api/v1/dashboard/summary", headers=auth).json()
    assert dashboard["income_minor"] == 1_000_000
    assert dashboard["expense_minor"] == 0
    assert dashboard["balance_minor"] == 700_000
    movements = client.get("/api/v1/transactions", headers=auth).json()["items"]
    assert {item["financial_role"] for item in movements} == {
        "regular",
        "debt_payment",
        "savings_transfer",
    }
