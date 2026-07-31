import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.infrastructure.database import get_db
from app.modules.auth.dependencies import CurrentUser
from app.modules.voice.schemas import (
    AudioTranscriptionResponse,
    VoiceInteractionUpdate,
    VoiceInterpretationRequest,
    VoiceInterpretationResponse,
)
from app.modules.voice.service import interpret_transcript, update_voice_interaction
from app.modules.voice.transcription import (
    ALLOWED_AUDIO_TYPES,
    MAX_AUDIO_BYTES,
    AudioInput,
    AudioTranscriber,
    get_audio_transcriber,
)

router = APIRouter(prefix="/voice", tags=["Voice"])
DbSession = Annotated[Session, Depends(get_db)]
Transcriber = Annotated[AudioTranscriber, Depends(get_audio_transcriber)]


@router.post("/interpretations", response_model=VoiceInterpretationResponse)
def create_interpretation(
    payload: VoiceInterpretationRequest,
    user: CurrentUser,
    db: DbSession,
) -> VoiceInterpretationResponse:
    return interpret_transcript(db, user, payload)


@router.patch("/interactions/{interaction_id}", status_code=204)
def finalize_interaction(
    interaction_id: uuid.UUID,
    payload: VoiceInteractionUpdate,
    user: CurrentUser,
    db: DbSession,
) -> None:
    update_voice_interaction(db, user, interaction_id, payload)


@router.post("/transcriptions", response_model=AudioTranscriptionResponse)
async def create_transcription(
    user: CurrentUser,
    transcriber: Transcriber,
    file: Annotated[UploadFile, File(...)],
) -> AudioTranscriptionResponse:
    del user
    content_type = file.content_type or "application/octet-stream"
    if content_type not in ALLOWED_AUDIO_TYPES:
        await file.close()
        raise AppError(
            status=415,
            title="Unsupported audio format",
            detail="Use M4A, MP4, MP3, WAV or WebM audio.",
            error_type="unsupported_audio_format",
        )

    content = bytearray()
    try:
        while chunk := await file.read(64 * 1024):
            content.extend(chunk)
            if len(content) > MAX_AUDIO_BYTES:
                raise AppError(
                    status=413,
                    title="Audio too large",
                    detail="Audio files cannot exceed 5 MB.",
                    error_type="audio_too_large",
                )
        if not content:
            raise AppError(
                status=422,
                title="Empty audio",
                detail="The audio file is empty.",
                error_type="empty_audio",
            )
        result = await transcriber.transcribe(
            AudioInput(
                content=bytes(content),
                filename=file.filename or "recording",
                content_type=content_type,
            )
        )
        return AudioTranscriptionResponse(
            transcript=result.transcript,
            provider=result.provider,
        )
    finally:
        content.clear()
        await file.close()
