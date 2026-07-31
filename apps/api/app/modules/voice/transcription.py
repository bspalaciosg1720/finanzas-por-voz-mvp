from dataclasses import dataclass
from typing import Protocol

from app.core.errors import AppError

MAX_AUDIO_BYTES = 5 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {
    "audio/m4a",
    "audio/mp4",
    "audio/mpeg",
    "audio/wav",
    "audio/webm",
    "audio/x-m4a",
}


@dataclass(frozen=True)
class AudioInput:
    content: bytes
    filename: str
    content_type: str


@dataclass(frozen=True)
class TranscriptionResult:
    transcript: str
    provider: str


class AudioTranscriber(Protocol):
    async def transcribe(self, audio: AudioInput) -> TranscriptionResult: ...


class DisabledTranscriber:
    async def transcribe(self, audio: AudioInput) -> TranscriptionResult:
        raise AppError(
            status=503,
            title="Transcription unavailable",
            detail="Automatic transcription is not configured.",
            error_type="transcription_unavailable",
        )


class FakeTranscriber:
    """Deterministic adapter for automated tests only."""

    def __init__(self, transcript: str = "Gasté 18 mil en almuerzo") -> None:
        self.transcript = transcript
        self.received: list[AudioInput] = []

    async def transcribe(self, audio: AudioInput) -> TranscriptionResult:
        self.received.append(audio)
        return TranscriptionResult(transcript=self.transcript, provider="fake")


def get_audio_transcriber() -> AudioTranscriber:
    return DisabledTranscriber()
