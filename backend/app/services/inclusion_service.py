from __future__ import annotations

from app.models.schemas import InclusionInput, InclusionResponse


def recommend_inclusion_support(payload: InclusionInput) -> InclusionResponse:
    income_score = min(payload.monthly_income / 50000, 1.0) * 40
    cibil_score = ((payload.cibil_score - 300) / 600) * 60
    alternative_credit_score = max(min(income_score + cibil_score, 100), 0)

    schemes: list[str] = []
    if payload.monthly_income < 25000:
        schemes.append("PM SVANidhi micro-credit support for small vendors")
        schemes.append("MUDRA Shishu/Kishore loan eligibility screening")
    if payload.monthly_income < 18000:
        schemes.append("State livelihood mission and subsidized SHG linkage")
    if payload.cibil_score < 650:
        schemes.append("Credit counseling and assisted repayment plan")

    microloan_options = [
        "NBFC-assisted microloan (small-ticket working capital)",
        "Joint liability group lending",
        "SHG-based community lending channels",
    ]
    literacy_content = [
        "How EMI works and why debt-to-income matters",
        "3-step process to improve credit score in 6 months",
        "Emergency fund basics for informal income households",
    ]

    return InclusionResponse(
        alternative_credit_score=round(alternative_credit_score, 2),
        eligible_schemes=schemes,
        microloan_options=microloan_options,
        literacy_content=literacy_content,
    )

