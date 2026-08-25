def auth_headers(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "alertas-inteligentes@example.com",
            "password": "Clave-segura-2026",
            "full_name": "Ana Alertas",
            "country_code": "CO",
            "timezone": "America/Bogota",
            "default_currency": "COP",
        },
    )
    return {"Authorization": f"Bearer {response.json()['tokens']['access_token']}"}


def test_alerts_are_prioritized_and_can_be_dismissed(client):
    headers = auth_headers(client)
    created = client.post(
        "/api/v1/debts",
        headers=headers,
        json={
            "name": "Tarjeta casi pagada",
            "debt_type": "credit_card",
            "initial_balance_minor": 1_000_000,
            "current_balance_minor": 100_000,
            "minimum_payment_minor": 50_000,
            "currency": "COP",
        },
    )
    assert created.status_code == 201

    response = client.get("/api/v1/financial-alerts", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_candidates"] == 1
    assert body["items"][0]["kind"] == "debt_progress"
    assert body["items"][0]["priority"] == 3

    dismissed = client.post(
        "/api/v1/financial-alerts/dismiss",
        headers=headers,
        json={"key": body["items"][0]["key"]},
    )
    assert dismissed.status_code == 204
    repeated = client.post(
        "/api/v1/financial-alerts/dismiss",
        headers=headers,
        json={"key": body["items"][0]["key"]},
    )
    assert repeated.status_code == 204
    assert client.get("/api/v1/financial-alerts", headers=headers).json()["items"] == []
