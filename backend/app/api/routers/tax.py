from fastapi import APIRouter

from app.models.schemas import (
    TaxAssistantInput,
    TaxAssistantResponse,
    TextExtractionInput,
    TextExtractionResponse,
)
from app.services.tax_service import estimate_tax, extract_entities

router = APIRouter()


@router.post("/estimate", response_model=TaxAssistantResponse)
def estimate_user_tax(payload: TaxAssistantInput) -> TaxAssistantResponse:
    return estimate_tax(payload)


@router.post("/extract", response_model=TextExtractionResponse)
def extract_tax_entities(payload: TextExtractionInput) -> TextExtractionResponse:
    return extract_entities(payload.text)

