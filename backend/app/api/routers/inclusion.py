from fastapi import APIRouter

from app.models.schemas import InclusionInput, InclusionResponse
from app.services.inclusion_service import recommend_inclusion_support

router = APIRouter()


@router.post("/recommend", response_model=InclusionResponse)
def inclusion_recommend(payload: InclusionInput) -> InclusionResponse:
    return recommend_inclusion_support(payload)

