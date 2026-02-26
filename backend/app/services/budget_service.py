from __future__ import annotations

import numpy as np

from app.models.schemas import (
    BudgetForecastInput,
    BudgetForecastResponse,
    ExpenseCategorizationInput,
    ExpenseCategorizationResponse,
)

CATEGORY_KEYWORDS = {
    "food": ["food", "grocery", "restaurant", "swiggy", "zomato"],
    "transport": ["fuel", "petrol", "metro", "uber", "ola", "transport"],
    "utilities": ["electricity", "water", "gas", "internet", "mobile", "bill"],
    "rent": ["rent", "house", "landlord"],
    "health": ["hospital", "medical", "pharmacy", "medicine"],
    "education": ["school", "college", "tuition", "course"],
    "business": ["inventory", "supplier", "shop", "wholesale"],
}


def forecast_next_month(payload: BudgetForecastInput) -> BudgetForecastResponse:
    history = np.array(payload.monthly_expense_history, dtype=float)
    weights = np.arange(1, len(history) + 1, dtype=float)
    weighted_avg = float(np.average(history, weights=weights))

    x = np.arange(len(history))
    slope = float(np.polyfit(x, history, 1)[0]) if len(history) >= 3 else 0.0
    trend_adjustment = slope * 0.5
    prediction = max(weighted_avg + trend_adjustment, 0.0)

    std_dev = float(np.std(history))
    lower = max(prediction - std_dev, 0.0)
    upper = prediction + std_dev

    if slope > 150:
        trend = "rising"
    elif slope < -150:
        trend = "falling"
    else:
        trend = "stable"

    return BudgetForecastResponse(
        next_month_prediction=round(prediction, 2),
        confidence_band={"lower": round(lower, 2), "upper": round(upper, 2)},
        trend=trend,
    )


def categorize_expenses(payload: ExpenseCategorizationInput) -> ExpenseCategorizationResponse:
    result: dict[str, float] = {k: 0.0 for k in CATEGORY_KEYWORDS}
    uncategorized = 0

    for tx in payload.transactions:
        description = tx.description.lower()
        assigned = False
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(word in description for word in keywords):
                result[category] += tx.amount
                assigned = True
                break
        if not assigned:
            uncategorized += 1

    rounded = {k: round(v, 2) for k, v in result.items() if v > 0}
    return ExpenseCategorizationResponse(
        categorized_expenses=rounded,
        uncategorized_count=uncategorized,
    )

