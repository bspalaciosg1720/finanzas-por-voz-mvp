from datetime import UTC, datetime


def auth_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "deudas@example.com",
            "password": "Clave-segura-2026",
            "full_name": "Ana Deudas",
            "country_code": "CO",
            "timezone": "America/Bogota",
            "default_currency": "COP",
        },
    )
    return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}


def test_debt_payment_updates_balance_and_status(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/v1/debts",
        headers=headers,
        json={
            "name": "Tarjeta principal",
            "debt_type": "credit_card",
            "initial_balance_minor": 500_000,
            "minimum_payment_minor": 50_000,
            "currency": "COP",
            "annual_interest_rate_bps": 2400,
            "payment_day": 15,
        },
    )
    assert created.status_code == 201
    debt_id = created.json()["id"]
    payment_payload = {
        "amount_minor": 500_000,
        "payment_type": "extra",
        "paid_at": datetime.now(UTC).isoformat(),
        "note": "Pago total",
    }
    payment_headers = {
        **headers,
        "Idempotency-Key": "44444444-4444-4444-8444-444444444444",
    }
    payment = client.post(
        f"/api/v1/debts/{debt_id}/payments",
        headers=payment_headers,
        json=payment_payload,
    )
    assert payment.status_code == 201
    repeated = client.post(
        f"/api/v1/debts/{debt_id}/payments",
        headers=payment_headers,
        json=payment_payload,
    )
    assert repeated.status_code == 201
    assert repeated.json()["id"] == payment.json()["id"]
    conflict = client.post(
        f"/api/v1/debts/{debt_id}/payments",
        headers=payment_headers,
        json={**payment_payload, "amount_minor": 100_000},
    )
    assert conflict.status_code == 409
    payment_id = payment.json()["id"]
    debt = client.get("/api/v1/debts", headers=headers).json()[0]
    assert debt["current_balance_minor"] == 0
    assert debt["status"] == "paid"
    assert debt["progress_percent"] == 100.0
    corrected = client.patch(
        f"/api/v1/debts/{debt_id}/payments/{payment_id}",
        headers=headers,
        json={"amount_minor": 300_000},
    )
    assert corrected.status_code == 200
    assert (
        client.get("/api/v1/debts", headers=headers).json()[0]["current_balance_minor"] == 200_000
    )
    removed = client.delete(f"/api/v1/debts/{debt_id}/payments/{payment_id}", headers=headers)
    assert removed.status_code == 204
    assert (
        client.get("/api/v1/debts", headers=headers).json()[0]["current_balance_minor"] == 500_000
    )


def test_plan_exposes_missing_rate_limitation(client):
    headers = auth_headers(client)
    response = client.post(
        "/api/v1/debts",
        headers=headers,
        json={
            "name": "Préstamo familiar",
            "debt_type": "personal_loan",
            "initial_balance_minor": 800_000,
            "minimum_payment_minor": 80_000,
            "currency": "COP",
        },
    )
    assert response.status_code == 201
    plan = client.get("/api/v1/debts/payoff-plan?strategy=snowball", headers=headers)
    assert plan.status_code == 200
    assert plan.json()["estimated_interest_minor"] is None
    assert plan.json()["limitations"]
