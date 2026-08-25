from datetime import UTC, datetime


def register_and_login(client):
    payload = {
        "email": "salud@example.com",
        "password": "Clave-segura-2026",
        "full_name": "Ana Salud",
        "country_code": "CO",
        "timezone": "America/Bogota",
        "default_currency": "COP",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    token = response.json()["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_health_requires_income_for_score(client):
    headers = register_and_login(client)
    response = client.get("/api/v1/financial-health/summary", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["score"] is None
    assert body["status"] == "Necesitamos más datos"
    assert body["confidence"] == "baja"


def test_health_score_is_deterministic_and_explained(client):
    headers = register_and_login(client)
    food_response = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Alimentación", "icon": "food", "movement_scope": "expense"},
    )
    assert food_response.status_code == 201
    food = food_response.json()
    occurred_at = datetime.now(UTC).isoformat()
    for movement_type, amount, category_id, key in (
        ("income", 3_000_000, None, "11111111-1111-4111-8111-111111111111"),
        ("expense", 1_200_000, food["id"], "22222222-2222-4222-8222-222222222222"),
    ):
        response = client.post(
            "/api/v1/transactions",
            headers={**headers, "Idempotency-Key": key},
            json={
                "type": movement_type,
                "amount_minor": amount,
                "currency": "COP",
                "category_id": category_id,
                "description": "Prueba",
                "occurred_at": occurred_at,
                "source": "manual",
            },
        )
        assert response.status_code == 201

    body = client.get("/api/v1/financial-health/summary", headers=headers).json()
    assert body["score"] == 62
    assert body["essential_percent"] == 40.0
    assert body["available_cash_minor"] == 1_800_000
    assert len(body["components"]) == 4
    assert 1 <= len(body["recommendations"]) <= 3


def test_patterns_use_closed_months_and_deterministic_amounts(client):
    headers = register_and_login(client)
    category = client.post(
        "/api/v1/categories",
        headers=headers,
        json={"name": "Domicilios", "icon": "food", "movement_scope": "expense"},
    ).json()
    now = datetime.now(UTC)
    periods = []
    year, month = now.year, now.month
    for _ in range(3):
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
        periods.append((year, month))
    periods.reverse()
    for index, ((year, month), expense) in enumerate(
        zip(periods, (100_000, 130_000, 170_000), strict=True), start=1
    ):
        occurred_at = datetime(year, month, 15, 17, tzinfo=UTC).isoformat()
        for kind, amount, category_id, suffix in (
            ("income", 150_000, None, 0),
            ("expense", expense, category["id"], 1),
        ):
            response = client.post(
                "/api/v1/transactions",
                headers={
                    **headers,
                    "Idempotency-Key": f"66666666-6666-4666-8666-{index:011d}{suffix}",
                },
                json={
                    "type": kind,
                    "amount_minor": amount,
                    "currency": "COP",
                    "category_id": category_id,
                    "description": "Serie histórica",
                    "occurred_at": occurred_at,
                    "source": "manual",
                },
            )
            assert response.status_code == 201

    response = client.get("/api/v1/financial-health/patterns", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["periods"] == [f"{year:04d}-{month:02d}" for year, month in periods]
    patterns = {item["key"]: item for item in body["patterns"]}
    assert patterns["expense_growth"]["change_percent"] == 70.0
    assert patterns["category_growth"]["category_name"] == "Domicilios"
    assert patterns["category_growth"]["previous_amount_minor"] == 130_000
    assert patterns["category_growth"]["current_amount_minor"] == 170_000


def test_variable_income_profile_uses_lower_quartile_as_conservative_base(client):
    headers = register_and_login(client)
    now = datetime.now(UTC)
    periods = []
    year, month = now.year, now.month
    for _ in range(6):
        year, month = (year - 1, 12) if month == 1 else (year, month - 1)
        periods.append((year, month))
    periods.reverse()
    for index, ((year, month), amount) in enumerate(
        zip(periods, (1_000_000, 2_000_000) * 3, strict=True), start=1
    ):
        response = client.post(
            "/api/v1/transactions",
            headers={
                **headers,
                "Idempotency-Key": f"77777777-7777-4777-8777-{index:012d}",
            },
            json={
                "type": "income",
                "amount_minor": amount,
                "currency": "COP",
                "category_id": None,
                "description": "Ingreso variable",
                "occurred_at": datetime(year, month, 15, 17, tzinfo=UTC).isoformat(),
                "source": "manual",
            },
        )
        assert response.status_code == 201

    response = client.get("/api/v1/financial-health/income-profile", headers=headers)
    assert response.status_code == 200
    profile = response.json()
    assert profile["classification"] == "variable"
    assert profile["average_income_minor"] == 1_500_000
    assert profile["median_income_minor"] == 1_500_000
    assert profile["conservative_income_minor"] == 1_000_000
    assert profile["variability_percent"] == 33.3


def test_extra_income_distribution_is_read_only_and_rule_based(client):
    headers = register_and_login(client)
    debt = client.post(
        "/api/v1/debts",
        headers=headers,
        json={
            "name": "Crédito personal",
            "debt_type": "personal_loan",
            "initial_balance_minor": 2_000_000,
            "minimum_payment_minor": 100_000,
            "currency": "COP",
        },
    )
    assert debt.status_code == 201

    response = client.get(
        "/api/v1/financial-health/extra-income?amount_minor=1000000",
        headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["detected"] is True
    assert body["source"] == "supplied"
    assert body["applied"] is False
    assert body["extra_income_minor"] == 1_000_000
    assert [(item["destination"], item["amount_minor"]) for item in body["allocations"]] == [
        ("debt", 700_000),
        ("goals", 300_000),
    ]
    unchanged = client.get("/api/v1/debts", headers=headers).json()[0]
    assert unchanged["current_balance_minor"] == 2_000_000
