from fastapi import APIRouter

from app.services.risk_model_manager import risk_model_manager

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "finaware-api"}


@router.get("/status")
def model_status() -> dict[str, str | bool | None]:
    return {
        "risk_model_trained": risk_model_manager.is_trained,
        "risk_best_model": risk_model_manager.best_model_name,
        "risk_trained_at": risk_model_manager.trained_at,
    }

