from fastapi import APIRouter, HTTPException

from app.models.schemas import LoanRecommendationRequest, LoanRecommendationResponse
from app.services.loan_service import recommend_loans

router = APIRouter()


@router.post("/recommend", response_model=LoanRecommendationResponse)
def recommend_loan(payload: LoanRecommendationRequest) -> LoanRecommendationResponse:
    try:
        return LoanRecommendationResponse(**recommend_loans(payload))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
