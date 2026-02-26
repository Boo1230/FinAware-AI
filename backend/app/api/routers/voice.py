from fastapi import APIRouter

from app.models.schemas import (
    TranslationInput,
    TranslationResponse,
    VoiceIntentInput,
    VoiceIntentResponse,
)
from app.services.assist_service import classify_intent, translate_text

router = APIRouter()


@router.post("/translate", response_model=TranslationResponse)
def translate(payload: TranslationInput) -> TranslationResponse:
    return translate_text(payload)


@router.post("/voice-intent", response_model=VoiceIntentResponse)
def voice_intent(payload: VoiceIntentInput) -> VoiceIntentResponse:
    return classify_intent(payload.text)

