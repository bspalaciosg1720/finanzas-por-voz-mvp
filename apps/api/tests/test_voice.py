import uuid

from app.modules.categories.models import Category
from app.modules.transactions.models import Transaction
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.test_transactions import auth_headers, register


def seed_category(
    db_factory: sessionmaker[Session],
    *,
    name: str,
    slug: str,
) -> Category:
    with db_factory() as db:
        category = Category(
            id=uuid.uuid4(),
            user_id=None,
            name=name,
            slug=slug,
            icon="test",
            movement_scope="expense",
            is_system=True,
            is_active=True,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category


def test_interprets_expense_amount_category_and_relative_date(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "voice-expense@example.com")
    category = seed_category(db_factory, name="Transporte", slug="transporte")

    response = client.post(
        "/api/v1/voice/interpretations",
        headers=auth_headers(auth),
        json={
            "transcript": "Ayer compré gasolina por noventa mil",
            "reference_at": "2026-07-30T12:00:00-05:00",
        },
    )

    assert response.status_code == 200
    interpretation = response.json()
    assert interpretation["movement_type"] == "expense"
    assert interpretation["amount_minor"] == 90_000
    assert interpretation["category_id"] == str(category.id)
    assert interpretation["category_name"] == "Transporte"
    assert interpretation["description"] == "Gasolina"
    assert interpretation["occurred_at"].startswith("2026-07-29T12:00:00")
    assert interpretation["requires_confirmation"] is True
    assert interpretation["ambiguities"] == []


def test_interprets_income_and_exposes_uncertain_category(client: TestClient) -> None:
    auth = register(client, "voice-income@example.com")
    response = client.post(
        "/api/v1/voice/interpretations",
        headers=auth_headers(auth),
        json={
            "transcript": "Me pagaron un millón de salario",
            "reference_at": "2026-07-30T12:00:00-05:00",
        },
    )

    interpretation = response.json()
    assert interpretation["movement_type"] == "income"
    assert interpretation["amount_minor"] == 1_000_000
    assert interpretation["category_id"] is None
    assert "category_uncertain" in interpretation["ambiguities"]


def test_ambiguous_transcript_is_not_forced_or_persisted(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "voice-ambiguous@example.com")
    response = client.post(
        "/api/v1/voice/interpretations",
        headers=auth_headers(auth),
        json={
            "transcript": "Fueron 20.000 o 30.000",
            "reference_at": "2026-07-30T12:00:00-05:00",
        },
    )

    interpretation = response.json()
    assert interpretation["movement_type"] is None
    assert interpretation["amount_minor"] is None
    assert "movement_type_uncertain" in interpretation["ambiguities"]
    assert "multiple_amounts" in interpretation["ambiguities"]
    with db_factory() as db:
        assert db.query(Transaction).count() == 0


def test_interpretation_requires_authentication_and_valid_reference(
    client: TestClient,
) -> None:
    assert (
        client.post(
            "/api/v1/voice/interpretations",
            json={"transcript": "Gasté 18 mil en almuerzo"},
        ).status_code
        == 401
    )
    auth = register(client, "voice-validation@example.com")
    assert (
        client.post(
            "/api/v1/voice/interpretations",
            headers=auth_headers(auth),
            json={
                "transcript": "Gasté 18 mil en almuerzo",
                "reference_at": "2026-07-30T12:00:00",
            },
        ).status_code
        == 422
    )
