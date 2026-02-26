from __future__ import annotations

from app.models.schemas import GoalPlanningInput, GoalPlanningResponse


def generate_goal_plan(payload: GoalPlanningInput) -> GoalPlanningResponse:
    remaining_amount = max(payload.target_price - payload.current_saved, 0)
    monthly_target = remaining_amount / payload.time_horizon_months
    current_surplus = max(payload.monthly_income - payload.monthly_expenses, 0)
    progress = (payload.current_saved / payload.target_price) * 100 if payload.target_price else 0

    if current_surplus > 0:
        projected_completion = remaining_amount / current_surplus if remaining_amount else 0
    else:
        projected_completion = float(payload.time_horizon_months) * 1.4

    base_needs = payload.monthly_income * 0.6
    base_wants = payload.monthly_income * 0.2
    base_savings = payload.monthly_income * 0.2
    extra_required = max(monthly_target - base_savings, 0)

    adjusted_budget = {
        "needs": round(max(base_needs - (extra_required * 0.35), 0), 2),
        "wants": round(max(base_wants - (extra_required * 0.65), 0), 2),
        "savings_goal": round(base_savings + extra_required, 2),
    }

    notes = []
    if monthly_target > current_surplus:
        notes.append(
            "Current surplus is lower than required monthly target; reduce discretionary spending or extend timeline."
        )
    else:
        notes.append("Target is achievable within current cash flow if savings discipline is maintained.")
    if progress >= 50:
        notes.append("You are already past 50% progress. Keep contribution frequency consistent.")

    return GoalPlanningResponse(
        goal_name=payload.goal_name,
        monthly_saving_target=round(monthly_target, 2),
        current_progress_pct=round(progress, 2),
        projected_completion_months=round(projected_completion, 2),
        adjusted_budget_plan=adjusted_budget,
        notes=notes,
    )

