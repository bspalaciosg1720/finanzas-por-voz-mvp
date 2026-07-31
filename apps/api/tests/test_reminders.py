import asyncio
import uuid
from datetime import UTC, datetime

from app.modules.notifications.delivery import FakePushSender
from app.modules.reminders.models import ReminderDelivery
from app.modules.reminders.service import evaluate_reminders
from app.modules.reminders.worker import run_reminder_batch
from app.modules.users.models import User
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.test_budget_alerts import expense
from tests.test_budgets import add_budget, seed_expense_category
from tests.test_push_devices import add_device
from tests.test_transactions import auth_headers, create, payload, register


def preferences_payload(**overrides: object) -> dict:
    values = {
        "daily_expense_enabled": True,
        "weekly_income_enabled": True,
        "budget_alerts_enabled": True,
        "local_hour": 20,
        "local_minute": 0,
    }
    values.update(overrides)
    return values


def test_reminder_preferences_are_opt_in_and_user_owned(client: TestClient) -> None:
    owner = register(client, "reminders@example.com")
    other = register(client, "other-reminders@example.com")

    defaults = client.get(
        "/api/v1/reminders/preferences", headers=auth_headers(owner)
    ).json()
    assert defaults["daily_expense_enabled"] is False
    assert defaults["weekly_income_enabled"] is False
    assert defaults["timezone"] == "America/Bogota"

    response = client.put(
        "/api/v1/reminders/preferences",
        headers=auth_headers(owner),
        json=preferences_payload(local_hour=19, local_minute=30),
    )
    assert response.status_code == 200
    assert response.json()["local_hour"] == 19
    assert (
        client.get(
            "/api/v1/reminders/preferences", headers=auth_headers(other)
        ).json()["daily_expense_enabled"]
        is False
    )


def test_reminder_preference_rejects_invalid_time(client: TestClient) -> None:
    auth = register(client, "invalid-reminder@example.com")
    response = client.put(
        "/api/v1/reminders/preferences",
        headers=auth_headers(auth),
        json=preferences_payload(local_hour=24),
    )
    assert response.status_code == 422


def test_evaluation_is_due_after_local_time_and_idempotent(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "due-reminder@example.com")
    client.put(
        "/api/v1/reminders/preferences",
        headers=auth_headers(auth),
        json=preferences_payload(),
    )
    user_id = uuid.UUID(auth["user"]["id"])
    sunday_at_8_pm_bogota = datetime(2026, 8, 3, 1, 0, tzinfo=UTC)
    with db_factory() as db:
        user = db.get(User, user_id)
        assert user is not None
        first = evaluate_reminders(db, user, now=sunday_at_8_pm_bogota)
        second = evaluate_reminders(db, user, now=sunday_at_8_pm_bogota)
    assert {item.kind for item in first.candidates} == {
        "missing_daily_expense",
        "missing_weekly_income",
    }
    assert second.candidates == []


def test_evaluation_suppresses_reminder_when_movement_exists(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "movement-reminder@example.com")
    client.put(
        "/api/v1/reminders/preferences",
        headers=auth_headers(auth),
        json=preferences_payload(weekly_income_enabled=False),
    )
    create(
        client,
        auth,
        payload(amount=20_000, occurred_at="2026-08-02T12:00:00-05:00"),
    )
    with db_factory() as db:
        user = db.get(User, uuid.UUID(auth["user"]["id"]))
        assert user is not None
        result = evaluate_reminders(
            db, user, now=datetime(2026, 8, 3, 1, 0, tzinfo=UTC)
        )
    assert result.candidates == []


def test_worker_delivers_pending_reminders_and_marks_them(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "worker-reminder@example.com")
    client.put(
        "/api/v1/reminders/preferences",
        headers=auth_headers(auth),
        json=preferences_payload(weekly_income_enabled=False),
    )
    assert add_device(client, auth).status_code == 201
    sender = FakePushSender()
    with db_factory() as db:
        result = asyncio.run(
            run_reminder_batch(
                db,
                sender,
                now=datetime(2026, 8, 3, 1, 0, tzinfo=UTC),
            )
        )
        delivery = db.query(ReminderDelivery).one()
        repeated = asyncio.run(
            run_reminder_batch(
                db,
                sender,
                now=datetime(2026, 8, 3, 1, 5, tzinfo=UTC),
            )
        )
    assert result.messages_sent == 1
    assert sender.sent[0].data["type"] == "missing_daily_expense"
    assert delivery.status == "delivered"
    assert delivery.delivered_at is not None
    assert repeated.messages_sent == 0


def test_disabled_delivery_keeps_reminder_pending_for_retry(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    from app.modules.notifications.delivery import DisabledPushSender

    auth = register(client, "disabled-worker@example.com")
    client.put(
        "/api/v1/reminders/preferences",
        headers=auth_headers(auth),
        json=preferences_payload(weekly_income_enabled=False),
    )
    add_device(client, auth)
    with db_factory() as db:
        result = asyncio.run(
            run_reminder_batch(
                db,
                DisabledPushSender(),
                now=datetime(2026, 8, 3, 1, 0, tzinfo=UTC),
            )
        )
        delivery = db.query(ReminderDelivery).one()
    assert result.messages_sent == 0
    assert delivery.status == "pending"


def test_worker_delivers_budget_alert_when_preference_is_enabled(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "budget-worker@example.com")
    client.put(
        "/api/v1/reminders/preferences",
        headers=auth_headers(auth),
        json=preferences_payload(
            daily_expense_enabled=False,
            weekly_income_enabled=False,
            budget_alerts_enabled=True,
        ),
    )
    add_device(client, auth)
    category = seed_expense_category(db_factory, name="Transporte")
    add_budget(client, auth, category.id, amount=100_000)
    create(client, auth, expense(category.id, 80_000))

    sender = FakePushSender()
    with db_factory() as db:
        result = asyncio.run(
            run_reminder_batch(
                db,
                sender,
                now=datetime(2026, 7, 31, 1, 0, tzinfo=UTC),
            )
        )
        repeated = asyncio.run(
            run_reminder_batch(
                db,
                sender,
                now=datetime(2026, 7, 31, 1, 5, tzinfo=UTC),
            )
        )
    assert result.messages_sent == 1
    assert sender.sent[0].data["type"] == "budget_warning"
    assert "Transporte" in sender.sent[0].body
    assert repeated.messages_sent == 0
