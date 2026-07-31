from app.modules.voice.transcription import (
    MAX_AUDIO_BYTES,
    FakeTranscriber,
    get_audio_transcriber,
)
from fastapi.testclient import TestClient
from tests.test_transactions import auth_headers, register


def post_audio(
    client: TestClient,
    auth: dict,
    *,
    content: bytes = b"synthetic-audio",
    content_type: str = "audio/m4a",
):
    return client.post(
        "/api/v1/voice/transcriptions",
        headers=auth_headers(auth),
        files={"file": ("recording.m4a", content, content_type)},
    )


def test_fake_transcriber_can_be_injected_without_provider_credentials(
    client: TestClient,
) -> None:
    auth = register(client, "fake-transcriber@example.com")
    fake = FakeTranscriber("Compré gasolina por 90 mil")
    client.app.dependency_overrides[get_audio_transcriber] = lambda: fake
    try:
        response = post_audio(client, auth)
    finally:
        client.app.dependency_overrides.pop(get_audio_transcriber, None)

    assert response.status_code == 200
    assert response.json() == {
        "transcript": "Compré gasolina por 90 mil",
        "provider": "fake",
    }
    assert len(fake.received) == 1
    assert fake.received[0].content == b"synthetic-audio"


def test_disabled_transcriber_returns_service_unavailable(client: TestClient) -> None:
    auth = register(client, "disabled-transcriber@example.com")
    response = post_audio(client, auth)
    assert response.status_code == 503
    assert response.json()["type"].endswith("/transcription_unavailable")


def test_transcription_rejects_unsupported_empty_and_oversized_audio(
    client: TestClient,
) -> None:
    auth = register(client, "invalid-audio@example.com")
    assert post_audio(client, auth, content_type="text/plain").status_code == 415
    assert post_audio(client, auth, content=b"").status_code == 422
    assert (
        post_audio(client, auth, content=b"x" * (MAX_AUDIO_BYTES + 1)).status_code
        == 413
    )


def test_transcription_requires_authentication(client: TestClient) -> None:
    response = client.post(
        "/api/v1/voice/transcriptions",
        files={"file": ("recording.m4a", b"audio", "audio/m4a")},
    )
    assert response.status_code == 401
