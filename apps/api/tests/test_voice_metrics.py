import uuid

from app.modules.voice.models import VoiceInteraction
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from tests.test_transactions import auth_headers, register


def interpret(client: TestClient, auth: dict, transcript: str) -> dict:
    response = client.post(
        "/api/v1/voice/interpretations",
        headers=auth_headers(auth),
        json={
            "transcript": transcript,
            "reference_at": "2026-07-30T12:00:00-05:00",
        },
    )
    assert response.status_code == 200
    return response.json()


def test_voice_metrics_store_no_financial_or_transcript_content(
    client: TestClient,
    db_factory: sessionmaker[Session],
) -> None:
    auth = register(client, "voice-metrics@example.com")
    result = interpret(client, auth, "Gasté 18 mil en almuerzo")

    completed = client.patch(
        f"/api/v1/voice/interactions/{result['interaction_id']}",
        headers=auth_headers(auth),
        json={
            "outcome": "completed",
            "corrected_fields": ["amount", "category", "amount"],
            "duration_ms": 4200,
        },
    )
    assert completed.status_code == 204

    with db_factory() as db:
        interaction = db.get(VoiceInteraction, uuid.UUID(result["interaction_id"]))
        assert interaction is not None
        assert interaction.status == "completed"
        assert interaction.corrected_fields == "amount,category"
        assert interaction.duration_ms == 4200
        columns = set(VoiceInteraction.__table__.columns.keys())
        assert not {"transcript", "amount_minor", "description", "audio"} & columns


def test_voice_metric_is_isolated_and_finalization_is_idempotent(
    client: TestClient,
) -> None:
    owner = register(client, "voice-metric-owner@example.com")
    other = register(client, "voice-metric-other@example.com")
    result = interpret(client, owner, "Fueron 20.000 o 30.000")
    path = f"/api/v1/voice/interactions/{result['interaction_id']}"

    assert (
        client.patch(
            path,
            headers=auth_headers(other),
            json={"outcome": "abandoned"},
        ).status_code
        == 404
    )
    assert (
        client.patch(
            path,
            headers=auth_headers(owner),
            json={"outcome": "completed", "corrected_fields": []},
        ).status_code
        == 204
    )
    assert (
        client.patch(
            path,
            headers=auth_headers(owner),
            json={"outcome": "abandoned"},
        ).status_code
        == 204
    )


def test_voice_metric_rejects_sensitive_or_unknown_correction_fields(
    client: TestClient,
) -> None:
    auth = register(client, "voice-metric-validation@example.com")
    result = interpret(client, auth, "Gasté 18 mil en almuerzo")
    response = client.patch(
        f"/api/v1/voice/interactions/{result['interaction_id']}",
        headers=auth_headers(auth),
        json={
            "outcome": "completed",
            "corrected_fields": ["transcript"],
        },
    )
    assert response.status_code == 422
