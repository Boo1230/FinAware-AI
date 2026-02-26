from fastapi import APIRouter

from app.models.schemas import GoalPlanningInput, GoalPlanningResponse
from app.services.planning_service import generate_goal_plan

router = APIRouter()


@router.post("/goal-plan", response_model=GoalPlanningResponse)
def goal_plan(payload: GoalPlanningInput) -> GoalPlanningResponse:
    return generate_goal_plan(payload)

