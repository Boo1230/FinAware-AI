from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.models.schemas import RiskAssessmentRequest, RiskAssessmentResponse, RiskTrainingResponse
from app.services.risk_model_manager import risk_model_manager
from app.services.risk_service import analyze_bank_statement, assess_risk, train_risk_model_from_csv

router = APIRouter()


@router.post("/assess", response_model=RiskAssessmentResponse)
def assess_loan_risk(payload: RiskAssessmentRequest) -> RiskAssessmentResponse:
    return assess_risk(payload)


@router.get("/training-schema")
def get_training_schema() -> dict:
    return risk_model_manager.expected_schema()


@router.post("/train", response_model=RiskTrainingResponse)
async def train_risk_model(
    file: UploadFile = File(...),
    target_column: str | None = Query(default=None),
) -> RiskTrainingResponse:
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV dataset is supported for training.")

    contents = await file.read()
    try:
        result = train_risk_model_from_csv(contents, target_column=target_column)
        return RiskTrainingResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Training failed: {exc}") from exc


@router.post("/bank-statement/analyze")
async def parse_bank_statement(file: UploadFile = File(...)) -> dict:
    contents = await file.read()
    try:
        return analyze_bank_statement(contents, filename=file.filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Statement analysis failed: {exc}") from exc
