import numpy as np
import pandas as pd

RISK_NUMERIC_FEATURES = [
    "monthly_income",
    "existing_emis",
    "collateral_value",
    "cibil_score",
    "active_loans",
    "monthly_expenses",
    "avg_monthly_balance",
    "savings_amount",
    "upi_transaction_frequency",
    "utility_bill_regularity",
    "transaction_consistency_score",
    "income_volatility_index",
    "debt_to_income_ratio",
    "income_stability_score",
    "savings_rate",
    "expense_ratio",
    "credit_utilization_ratio",
    "collateral_coverage_ratio",
]

RISK_CATEGORICAL_FEATURES = ["occupation", "location", "business_type"]
RISK_MODEL_FEATURES = RISK_NUMERIC_FEATURES + RISK_CATEGORICAL_FEATURES

CANONICAL_BASE_COLUMNS = {
    "monthly_income": ["monthly_income", "income", "monthlyincome"],
    "existing_emis": ["existing_emis", "emi", "monthly_emi"],
    "collateral_value": ["collateral_value", "collateral"],
    "cibil_score": ["cibil_score", "credit_score", "cibil"],
    "active_loans": ["active_loans", "number_of_active_loans", "loans_active"],
    "monthly_expenses": ["monthly_expenses", "expenses", "monthly_spend"],
    "avg_monthly_balance": ["avg_monthly_balance", "average_monthly_balance"],
    "savings_amount": ["savings_amount", "savings"],
    "upi_transaction_frequency": ["upi_transaction_frequency", "upi_txn_freq"],
    "utility_bill_regularity": ["utility_bill_regularity", "utility_regularity"],
    "transaction_consistency_score": [
        "transaction_consistency_score",
        "txn_consistency_score",
    ],
    "income_volatility_index": ["income_volatility_index", "income_volatility"],
    "occupation": ["occupation", "job"],
    "location": ["location", "city", "state"],
    "business_type": ["business_type", "business"],
}


def _safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0, np.nan)


def resolve_canonical_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed_df = df.copy()
    lower_map = {c.lower().strip(): c for c in renamed_df.columns}

    for canonical, aliases in CANONICAL_BASE_COLUMNS.items():
        if canonical in renamed_df.columns:
            continue
        resolved = None
        for alias in aliases:
            alias_key = alias.lower().strip()
            if alias_key in lower_map:
                resolved = lower_map[alias_key]
                break
        if resolved:
            renamed_df = renamed_df.rename(columns={resolved: canonical})
    return renamed_df


def prepare_risk_features(raw_df: pd.DataFrame) -> pd.DataFrame:
    df = resolve_canonical_columns(raw_df)

    default_numeric = {
        "monthly_income": 1.0,
        "existing_emis": 0.0,
        "collateral_value": 0.0,
        "cibil_score": 650.0,
        "active_loans": 0.0,
        "monthly_expenses": 0.0,
        "avg_monthly_balance": 0.0,
        "savings_amount": 0.0,
        "upi_transaction_frequency": 0.0,
        "utility_bill_regularity": 0.5,
        "transaction_consistency_score": 0.5,
        "income_volatility_index": 0.5,
    }
    default_categorical = {
        "occupation": "unknown",
        "location": "unknown",
        "business_type": "general",
    }

    for col, val in default_numeric.items():
        if col not in df.columns:
            df[col] = val
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(val)

    for col, val in default_categorical.items():
        if col not in df.columns:
            df[col] = val
        df[col] = df[col].fillna(val).astype(str).str.strip().str.lower()
        df.loc[df[col] == "", col] = val

    df["monthly_income"] = df["monthly_income"].clip(lower=1)
    df["cibil_score"] = df["cibil_score"].clip(lower=300, upper=900)
    df["utility_bill_regularity"] = df["utility_bill_regularity"].clip(0, 1)
    df["transaction_consistency_score"] = df["transaction_consistency_score"].clip(0, 1)

    df["debt_to_income_ratio"] = _safe_div(df["existing_emis"], df["monthly_income"]).fillna(0)
    df["income_stability_score"] = (1 / (1 + df["income_volatility_index"])).clip(0, 1)
    df["savings_rate"] = _safe_div(df["savings_amount"], df["monthly_income"]).fillna(0)
    df["expense_ratio"] = _safe_div(df["monthly_expenses"], df["monthly_income"]).fillna(0)
    df["credit_utilization_ratio"] = (
        _safe_div(df["existing_emis"] * (df["active_loans"] + 1), df["monthly_income"]).fillna(0)
    )
    df["collateral_coverage_ratio"] = _safe_div(
        df["collateral_value"], (df["existing_emis"] * 12) + 1
    ).fillna(0)

    for col in RISK_NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default_numeric.get(col, 0))
    return df[RISK_MODEL_FEATURES].copy()


def score_to_risk_category(default_probability: float) -> str:
    if default_probability < 30:
        return "Low"
    if default_probability < 60:
        return "Medium"
    return "High"

