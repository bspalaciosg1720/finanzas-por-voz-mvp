import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.categories.models import Category
from app.modules.users.models import User
from app.modules.voice.models import VoiceInteraction
from app.modules.voice.parser import parse_voice_text
from app.modules.voice.schemas import (
    FieldConfidence,
    VoiceInteractionUpdate,
    VoiceInterpretationRequest,
    VoiceInterpretationResponse,
)
from app.shared.time import utc_now


def interpret_transcript(
    db: Session,
    user: User,
    payload: VoiceInterpretationRequest,
) -> VoiceInterpretationResponse:
    parsed = parse_voice_text(
        payload.transcript,
        timezone=user.timezone,
        reference_at=payload.reference_at,
    )
    category = None
    if parsed.category_slug:
        category = db.scalar(
            select(Category).where(
                Category.slug == parsed.category_slug,
                Category.is_active.is_(True),
                or_(Category.user_id.is_(None), Category.user_id == user.id),
            )
        )

    ambiguities = list(parsed.ambiguities)
    if parsed.category_slug and category is None:
        ambiguities.append("category_unavailable")

    interaction = VoiceInteraction(
        user_id=user.id,
        ambiguity_count=len(ambiguities),
    )
    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return VoiceInterpretationResponse(
        interaction_id=interaction.id,
        transcript=payload.transcript,
        movement_type=parsed.movement_type,
        amount_minor=parsed.amount_minor,
        currency=user.default_currency,
        category_id=category.id if category else None,
        category_name=category.name if category else None,
        description=parsed.description,
        occurred_at=parsed.occurred_at,
        confidence=FieldConfidence(**parsed.confidence),
        ambiguities=ambiguities,
        requires_confirmation=True,
    )


def update_voice_interaction(
    db: Session,
    user: User,
    interaction_id: uuid.UUID,
    payload: VoiceInteractionUpdate,
) -> VoiceInteraction:
    interaction = db.scalar(
        select(VoiceInteraction).where(
            VoiceInteraction.id == interaction_id,
            VoiceInteraction.user_id == user.id,
        )
    )
    if interaction is None:
        raise AppError(
            status=404,
            title="Voice interaction not found",
            detail="The voice interaction does not exist.",
            error_type="voice_interaction_not_found",
        )
    if interaction.status != "interpreted":
        return interaction
    interaction.status = payload.outcome
    interaction.corrected_fields = ",".join(payload.corrected_fields)
    interaction.duration_ms = payload.duration_ms
    interaction.completed_at = utc_now()
    db.commit()
    db.refresh(interaction)
    return interaction
