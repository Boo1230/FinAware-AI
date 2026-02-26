from fastapi import APIRouter

from app.api.routers import budget, health, inclusion, insurance, loan, planning, risk, tax, voice

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(risk.router, prefix="/risk", tags=["risk"])
api_router.include_router(loan.router, prefix="/loans", tags=["loans"])
api_router.include_router(tax.router, prefix="/tax", tags=["tax"])
api_router.include_router(planning.router, prefix="/planning", tags=["planning"])
api_router.include_router(budget.router, prefix="/budget", tags=["budget"])
api_router.include_router(insurance.router, prefix="/insurance", tags=["insurance"])
api_router.include_router(inclusion.router, prefix="/inclusion", tags=["inclusion"])
api_router.include_router(voice.router, prefix="/assist", tags=["assist"])

