from __future__ import annotations

import csv
import os
import re
from pathlib import Path
from typing import Any

from app.models.schemas import LoanRecommendationItem, LoanRecommendationRequest


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    monthly_rate = annual_rate / 12 / 100
    if monthly_rate == 0:
        return principal / tenure_months
    factor = (1 + monthly_rate) ** tenure_months
    return principal * monthly_rate * factor / (factor - 1)


def _dataset_candidates() -> list[Path]:
    root = Path(__file__).resolve().parents[3]
    env_path = os.getenv("LOAN_DATASET_PATH", "").strip()

    candidates: list[Path] = []
    if env_path:
        candidates.append(Path(env_path).expanduser())

    candidates.extend(
        [
            root / "backend" / "data" / "india_loans_dataset.csv",
            root / "india_loans_dataset.csv",
            Path.home() / "Downloads" / "india_loans_dataset.csv",
        ]
    )
    return candidates


def _load_loan_catalog() -> tuple[list[dict[str, str]], Path]:
    for path in _dataset_candidates():
        if not path.exists() or not path.is_file():
            continue

        with path.open("r", encoding="utf-8-sig", newline="") as file:
            rows = [dict(row) for row in csv.DictReader(file)]
        rows = [row for row in rows if any((value or "").strip() for value in row.values())]
        if rows:
            return rows, path

    searched = ", ".join(str(path) for path in _dataset_candidates())
    raise FileNotFoundError(
        "Loan dataset not found. Set LOAN_DATASET_PATH or place india_loans_dataset.csv in one of: "
        f"{searched}"
    )


def _parse_tenure_months(tenure_years: str) -> tuple[int, int]:
    numbers = re.findall(r"\d+(?:\.\d+)?", str(tenure_years or ""))
    if not numbers:
        return (12, 60)

    values = [float(n) for n in numbers]
    minimum_years = min(values)
    maximum_years = max(values)
    min_months = max(1, int(round(minimum_years * 12)))
    max_months = max(min_months, int(round(maximum_years * 12)))
    return min_months, max_months


def _normalize_text(*parts: str) -> str:
    return " ".join(str(part or "").strip().lower() for part in parts)


def _secured_label(raw: str) -> str:
    text = str(raw or "").strip().lower()
    if "yes/no" in text:
        return "mixed"
    if text.startswith("yes"):
        return "yes"
    return "no"


def _estimate_interest_rate(row: dict[str, str], risk_category: str) -> float:
    loan_category = str(row.get("loan_category", "")).strip().lower()
    loan_type = str(row.get("loan_type", "")).strip().lower()
    lender_type = str(row.get("lender_type", "")).strip().lower()
    secured = _secured_label(str(row.get("secured", "")))

    category_base_rates: dict[str, float] = {
        "retail": 11.8,
        "business": 12.8,
        "agriculture": 8.4,
        "priority sector": 8.8,
        "government scheme": 9.2,
        "digital lending": 18.5,
        "rural": 11.2,
        "housing": 9.0,
    }
    base_rate = category_base_rates.get(loan_category, 12.5)

    # Specific loan type adjustments for a more realistic quote band.
    if "home loan" in loan_type or "affordable housing" in loan_type:
        base_rate = 8.7
    elif "education loan" in loan_type:
        base_rate = 10.2
    elif "gold loan" in loan_type:
        base_rate = 10.8
    elif "loan against property" in loan_type:
        base_rate = 10.5
    elif "personal loan" in loan_type:
        base_rate = 14.4
    elif "bnpl" in loan_type:
        base_rate = 21.0
    elif "merchant cash advance" in loan_type:
        base_rate = 22.0

    if secured == "yes":
        base_rate -= 1.0
    elif secured == "no":
        base_rate += 0.8

    if "fintech" in lender_type:
        base_rate += 1.0
    if "nbfc" in lender_type:
        base_rate += 0.5
    if "coop" in lender_type:
        base_rate -= 0.3

    risk_adjustment = {"Low": -0.7, "Medium": 0.0, "High": 1.5}[risk_category]
    base_rate += risk_adjustment

    return round(_clamp(base_rate, 6.5, 28.0), 2)


def _benefit_score(row: dict[str, str]) -> float:
    category = str(row.get("loan_category", "")).strip().lower()
    loan_type = str(row.get("loan_type", "")).strip().lower()

    if category == "government scheme":
        return 75.0
    if category == "priority sector":
        return 62.0
    if category == "agriculture":
        return 58.0
    if "home loan" in loan_type or category == "housing":
        return 52.0
    if "education loan" in loan_type:
        return 44.0
    if category == "business":
        return 26.0
    if category == "digital lending":
        return 8.0
    return 18.0


def _amount_range(row: dict[str, str]) -> tuple[float, float]:
    text = _normalize_text(
        row.get("loan_category", ""),
        row.get("loan_type", ""),
        row.get("sub_type", ""),
        row.get("target_segment", ""),
        row.get("notes", ""),
    )

    if "shishu" in text:
        return 10000, 50000
    if "kishore" in text:
        return 50000, 500000
    if "tarun" in text:
        return 500000, 1000000
    if "bnpl" in text:
        return 1000, 50000
    if "consumer durable" in text:
        return 5000, 200000
    if "instant personal" in text:
        return 5000, 250000
    if "two wheeler" in text:
        return 30000, 300000
    if "crop loan" in text or "kisan credit card" in text:
        return 10000, 500000
    if "education loan" in text and "abroad" in text:
        return 300000, 5000000
    if "education loan" in text:
        return 100000, 1500000
    if "vehicle loan" in text and "car" in text:
        return 150000, 2500000
    if "gold loan" in text:
        return 10000, 3000000
    if "home loan" in text or "affordable housing" in text:
        return 500000, 15000000
    if "loan against property" in text:
        return 500000, 25000000
    if "reverse mortgage" in text:
        return 500000, 10000000
    if "startup loan" in text:
        return 200000, 20000000
    if "invoice financing" in text or "trade finance" in text:
        return 50000, 10000000
    if "msme" in text or "equipment finance" in text:
        return 100000, 10000000
    if "merchant cash advance" in text:
        return 20000, 1000000
    if "self help group" in text or "joint liability group" in text:
        return 10000, 500000
    if "personal loan" in text:
        return 20000, 2000000
    return 50000, 3000000


def _amount_fit_score(requested_amount: float, min_amount: float, max_amount: float) -> float:
    if min_amount <= requested_amount <= max_amount:
        return 100.0

    if requested_amount < min_amount:
        gap = (min_amount - requested_amount) / max(min_amount, 1.0)
    else:
        gap = (requested_amount - max_amount) / max(max_amount, 1.0)

    return _clamp(100 - (gap * 160), 0.0, 100.0)


def _applicant_segments(payload: LoanRecommendationRequest) -> set[str]:
    text = _normalize_text(payload.occupation or "", payload.purpose or "")
    segments = {"individual"}

    if any(token in text for token in ["salaried", "salary", "employee"]):
        segments.add("salaried")
    if any(token in text for token in ["student", "study", "education", "college"]):
        segments.add("students")
    if any(token in text for token in ["farmer", "agri", "crop", "agriculture"]):
        segments.add("farmers")
    if any(
        token in text
        for token in [
            "business",
            "shop",
            "vendor",
            "merchant",
            "self employed",
            "self-employed",
            "sme",
            "msme",
            "startup",
            "entrepreneur",
            "trade",
        ]
    ):
        segments.add("business")
    if any(token in text for token in ["woman", "women", "female"]):
        segments.add("women")

    return segments


def _segment_fit_score(target_segment: str, applicant_segments: set[str]) -> float:
    target = str(target_segment or "").strip().lower()
    if not target:
        return 65.0

    individual_aliases = ("individual", "consumer", "existing borrower")
    business_aliases = ("business", "sme", "msme", "micro business", "small merchant", "entrepreneur")

    if any(alias in target for alias in individual_aliases):
        return 92.0 if "individual" in applicant_segments else 70.0
    if "salaried" in target:
        return 95.0 if "salaried" in applicant_segments else 62.0
    if "student" in target:
        return 98.0 if "students" in applicant_segments else 28.0
    if "farmer" in target:
        return 98.0 if "farmers" in applicant_segments else 28.0
    if any(alias in target for alias in business_aliases):
        return 95.0 if "business" in applicant_segments else 48.0
    if "women" in target or "sc/st/women" in target:
        return 90.0 if "women" in applicant_segments else 44.0
    if "senior" in target:
        return 35.0
    return 65.0


def _risk_product_multiplier(row: dict[str, str], risk_category: str) -> float:
    category = str(row.get("loan_category", "")).strip().lower()
    lender_type = str(row.get("lender_type", "")).strip().lower()
    secured = _secured_label(str(row.get("secured", "")))

    multiplier = 1.0
    scheme_or_priority = category in {"government scheme", "priority sector", "agriculture", "rural"}
    digital = category == "digital lending" or "fintech" in lender_type

    if risk_category == "High":
        multiplier -= 0.12
        if secured == "yes":
            multiplier += 0.20
        if scheme_or_priority:
            multiplier += 0.12
        if digital and secured == "no":
            multiplier -= 0.18
    elif risk_category == "Medium":
        if secured == "yes":
            multiplier += 0.08
        if scheme_or_priority:
            multiplier += 0.06
        if digital and secured == "no":
            multiplier -= 0.08
    else:  # Low risk
        if secured == "yes":
            multiplier += 0.03
        if digital and secured == "no":
            multiplier -= 0.03

    return _clamp(multiplier, 0.55, 1.30)


def _recommended_tenure(min_months: int, max_months: int, risk_category: str) -> int:
    if max_months <= min_months:
        return min_months

    if risk_category == "Low":
        tenure = int(round((0.25 * min_months) + (0.75 * max_months)))
    elif risk_category == "Medium":
        tenure = int(round((min_months + max_months) / 2))
    else:
        tenure = int(round((0.65 * min_months) + (0.35 * max_months)))
    return int(_clamp(tenure, min_months, max_months))


def recommend_loans(payload: LoanRecommendationRequest) -> dict[str, Any]:
    catalog_rows, _ = _load_loan_catalog()
    if not catalog_rows:
        raise ValueError("Loan catalog is empty.")

    applicant_segments = _applicant_segments(payload)
    rows_with_meta: list[tuple[dict[str, str], float, int, float, float, float]] = []
    for row in catalog_rows:
        annual_rate = _estimate_interest_rate(row, payload.risk_category)
        min_tenure, max_tenure = _parse_tenure_months(row.get("typical_tenure_years", ""))
        tenure = _recommended_tenure(min_tenure, max_tenure, payload.risk_category)
        min_amount, max_amount = _amount_range(row)
        fit_score = _amount_fit_score(payload.requested_amount, min_amount, max_amount)
        segment_score = _segment_fit_score(row.get("target_segment", ""), applicant_segments)
        rows_with_meta.append((row, annual_rate, tenure, fit_score, _benefit_score(row), segment_score))

    min_rate = min(item[1] for item in rows_with_meta)
    max_rate = max(item[1] for item in rows_with_meta)
    spread = max(max_rate - min_rate, 1e-6)

    ranked: list[LoanRecommendationItem] = []
    for row, annual_rate, tenure_months, fit_score, benefit_score, segment_score in rows_with_meta:
        low_interest_score = ((max_rate - annual_rate) / spread) * 100
        adjusted_approval = payload.approval_probability * _risk_product_multiplier(
            row, payload.risk_category
        )
        adjusted_approval = _clamp(adjusted_approval, 1.0, 99.5)
        annual_tax_savings = payload.requested_amount * (benefit_score / 100) * 0.08
        score = (
            adjusted_approval * 0.35
            + low_interest_score * 0.25
            + fit_score * 0.2
            + segment_score * 0.15
            + benefit_score * 0.05
        )
        estimated_emi = _emi(payload.requested_amount, annual_rate, max(tenure_months, 1))
        loan_type = str(row.get("loan_type", "")).strip()
        sub_type = str(row.get("sub_type", "")).strip()
        typical_lenders = str(row.get("typical_lenders", "")).strip()
        display_name = f"{loan_type} - {sub_type} ({typical_lenders})"
        ranked.append(
            LoanRecommendationItem(
                lender_name=display_name,
                loan_score=round(score, 2),
                estimated_emi=round(estimated_emi, 2),
                annual_interest_rate=annual_rate,
                annual_tax_savings=round(annual_tax_savings, 2),
                adjusted_approval_probability=round(adjusted_approval, 2),
            )
        )

    ranked = sorted(ranked, key=lambda x: x.loan_score, reverse=True)
    return {"best_option": ranked[0], "ranked_options": ranked[:10]}
