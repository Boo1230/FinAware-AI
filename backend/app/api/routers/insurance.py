from fastapi import APIRouter

from app.models.schemas import InsuranceInput, InsuranceResponse
from app.services.insurance_service import advise_insurance

router = APIRouter()


@router.post("/advise", response_model=InsuranceResponse)
def insurance_advice(payload: InsuranceInput) -> InsuranceResponse:
    return advise_insurance(payload)

