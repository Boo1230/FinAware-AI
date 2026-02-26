from __future__ import annotations

from app.models.schemas import InsuranceInput, InsuranceResponse


def advise_insurance(payload: InsuranceInput) -> InsuranceResponse:
    condition_factor = min(len(payload.health_conditions) * 0.08, 0.25)
    occupation_factor = {"low": 0.1, "medium": 0.2, "high": 0.35}[payload.occupation_risk_level]
    age_factor = min(max((payload.age - 18) / 62, 0), 1)
    family_factor = min(payload.family_members / 8, 1)

    risk_profile = (
        0.35 * age_factor
        + 0.25 * family_factor
        + 0.25 * occupation_factor
        + 0.15 * condition_factor
    ) * 100

    annual_income = payload.monthly_income * 12
    health_cover = max(500000, annual_income * 0.5 + payload.family_members * 100000)
    life_cover = max(annual_income * 10, 1000000)
    emergency_fund = payload.monthly_income * 6

    recommendations = [
        "Prioritize base health insurance with hospitalization + critical illness add-on.",
        "Maintain term life cover at least 10x annual income.",
        "Create emergency corpus in liquid savings over 6-9 months.",
    ]
    if payload.occupation_risk_level == "high":
        recommendations.append("Add accidental disability rider due to high occupation risk.")
    if payload.health_conditions:
        recommendations.append("Choose policy with lower waiting period for pre-existing conditions.")

    return InsuranceResponse(
        risk_profile_score=round(risk_profile, 2),
        health_insurance_cover=round(health_cover, 2),
        life_insurance_cover=round(life_cover, 2),
        emergency_fund_target=round(emergency_fund, 2),
        recommendations=recommendations,
    )

