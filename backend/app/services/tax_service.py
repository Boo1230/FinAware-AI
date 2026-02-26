from __future__ import annotations

import re
from typing import Any

from app.models.schemas import TaxAssistantInput, TaxAssistantResponse, TextExtractionResponse

PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
AMOUNT_REGEX = re.compile(r"(?:INR|Rs\.?|₹)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?|[0-9]+(?:\.[0-9]+)?)")
SECTIONS_REGEX = re.compile(r"\b80C|80D|80CCD|HRA|LTA\b", flags=re.IGNORECASE)


def _tax_from_old_regime(taxable_income: float) -> float:
    tax = 0.0
    slabs = [
        (250000, 0.0),
        (250000, 0.05),
        (500000, 0.2),
        (float("inf"), 0.3),
    ]
    remaining = taxable_income
    for cap, rate in slabs:
        if remaining <= 0:
            break
        segment = min(remaining, cap)
        tax += segment * rate
        remaining -= segment
    tax += tax * 0.04
    return tax


def estimate_tax(payload: TaxAssistantInput) -> TaxAssistantResponse:
    gross_income = payload.salary_income + payload.business_income + payload.other_income
    ded_80c = min(payload.investments_80c, 150000)
    ded_80d = min(payload.insurance_80d, 25000)
    other_ded = payload.other_deductions
    total_deductions = ded_80c + ded_80d + other_ded
    taxable_income = max(gross_income - total_deductions, 0)
    estimated_tax = _tax_from_old_regime(taxable_income)

    suggestions: list[str] = []
    if payload.investments_80c < 150000:
        suggestions.append(
            f"You can still claim up to INR {150000 - payload.investments_80c:.0f} under Section 80C."
        )
    if payload.insurance_80d < 25000:
        suggestions.append(
            f"You can still claim up to INR {25000 - payload.insurance_80d:.0f} under Section 80D."
        )
    if payload.other_deductions <= 0:
        suggestions.append("Review HRA/LTA and education-loan deductions if applicable.")
    if not suggestions:
        suggestions.append("Current deductions are near practical limits for this simplified tax model.")

    return TaxAssistantResponse(
        gross_income=round(gross_income, 2),
        taxable_income=round(taxable_income, 2),
        estimated_tax=round(estimated_tax, 2),
        deductions_applied={
            "80C": round(ded_80c, 2),
            "80D": round(ded_80d, 2),
            "other_deductions": round(other_ded, 2),
        },
        suggestions=suggestions,
    )


def extract_entities(text: str) -> TextExtractionResponse:
    pan_matches = list(set(PAN_REGEX.findall(text.upper())))
    amount_matches = [float(a.replace(",", "")) for a in AMOUNT_REGEX.findall(text)]
    sections = sorted({s.upper() for s in SECTIONS_REGEX.findall(text)})
    likely_income = sorted([a for a in amount_matches if a > 10000], reverse=True)[:3]

    return TextExtractionResponse(
        pan_numbers=pan_matches,
        amounts=amount_matches[:15],
        likely_income_amounts=likely_income,
        detected_sections=sections,
    )

