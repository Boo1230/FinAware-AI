from __future__ import annotations

from app.models.schemas import TranslationInput, TranslationResponse, VoiceIntentResponse

INTENT_MAP = {
    "loan_application": ["loan", "borrow", "emi", "interest", "credit"],
    "tax_help": ["tax", "deduction", "80c", "80d", "return"],
    "budget_tracking": ["budget", "expense", "spending", "save money"],
    "insurance_query": ["insurance", "health cover", "life cover", "policy"],
}


def classify_intent(text: str) -> VoiceIntentResponse:
    lower = text.lower()
    best_intent = "general_query"
    best_keywords: list[str] = []

    for intent, keywords in INTENT_MAP.items():
        matched = [kw for kw in keywords if kw in lower]
        if len(matched) > len(best_keywords):
            best_intent = intent
            best_keywords = matched

    confidence = 0.2 if not best_keywords else min(0.4 + 0.15 * len(best_keywords), 0.95)
    return VoiceIntentResponse(
        intent=best_intent,
        confidence=round(confidence, 2),
        matched_keywords=best_keywords,
    )


def translate_text(payload: TranslationInput) -> TranslationResponse:
    if payload.source_lang == payload.target_lang:
        return TranslationResponse(translated_text=payload.text, used_engine="identity")

    try:
        from deep_translator import GoogleTranslator

        translated = GoogleTranslator(
            source=payload.source_lang, target=payload.target_lang
        ).translate(payload.text)
        return TranslationResponse(translated_text=translated, used_engine="google_translator")
    except Exception:
        # Graceful fallback to keep API deterministic without external translator dependency.
        return TranslationResponse(
            translated_text=payload.text,
            used_engine="fallback_no_translator_installed",
        )

