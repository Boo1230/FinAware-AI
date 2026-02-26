from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.core.config import settings
from app.services.feature_engineering import (
    RISK_CATEGORICAL_FEATURES,
    RISK_MODEL_FEATURES,
    RISK_NUMERIC_FEATURES,
    prepare_risk_features,
    resolve_canonical_columns,
)


@dataclass
class ModelArtifact:
    model: Any
    best_model_name: str
    metrics: dict[str, dict[str, float]]
    target_column: str
    trained_features: list[str]
    trained_at: str


class RiskModelManager:
    def __init__(self, artifact_dir: str, filename: str) -> None:
        self.artifact_dir = Path(artifact_dir)
        self.artifact_path = self.artifact_dir / filename
        self.model: Any | None = None
        self.best_model_name: str | None = None
        self.metrics: dict[str, dict[str, float]] = {}
        self.target_column: str = settings.default_target_column
        self.trained_features = RISK_MODEL_FEATURES
        self.trained_at: str | None = None

        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    @property
    def is_trained(self) -> bool:
        return self.model is not None

    def load(self) -> None:
        if not self.artifact_path.exists():
            return
        payload: dict[str, Any] = joblib.load(self.artifact_path)
        self.model = payload["model"]
        self.best_model_name = payload["best_model_name"]
        self.metrics = payload["metrics"]
        self.target_column = payload["target_column"]
        self.trained_features = payload["trained_features"]
        self.trained_at = payload.get("trained_at")

    def save(self) -> None:
        if self.model is None or self.best_model_name is None:
            return
        payload = {
            "model": self.model,
            "best_model_name": self.best_model_name,
            "metrics": self.metrics,
            "target_column": self.target_column,
            "trained_features": self.trained_features,
            "trained_at": self.trained_at,
        }
        joblib.dump(payload, self.artifact_path)

    def expected_schema(self) -> dict[str, Any]:
        return {
            "required_features": [
                "monthly_income",
                "existing_emis",
                "collateral_value",
                "cibil_score",
                "occupation",
                "location",
                "business_type",
            ],
            "optional_features": [
                "active_loans",
                "monthly_expenses",
                "avg_monthly_balance",
                "savings_amount",
                "upi_transaction_frequency",
                "utility_bill_regularity",
                "transaction_consistency_score",
                "income_volatility_index",
            ],
            "target_column_examples": ["defaulted", "loan_default", "target", "label"],
            "target_meaning": "1 for default, 0 for non-default",
        }

    def _resolve_target_column(self, df: pd.DataFrame, requested_target: str | None) -> str:
        if requested_target and requested_target in df.columns:
            return requested_target

        lower_map = {c.lower().strip(): c for c in df.columns}
        if requested_target and requested_target.lower().strip() in lower_map:
            return lower_map[requested_target.lower().strip()]

        for candidate in ["defaulted", "loan_default", "target", "label", "default"]:
            if candidate in df.columns:
                return candidate
            if candidate in lower_map:
                return lower_map[candidate]

        raise ValueError(
            "Target column not found. Provide `target_column` or include one of "
            "[defaulted, loan_default, target, label, default]."
        )

    @staticmethod
    def _to_binary_target(series: pd.Series) -> pd.Series:
        mapping = {
            "yes": 1,
            "y": 1,
            "true": 1,
            "default": 1,
            "defaulted": 1,
            "1": 1,
            "no": 0,
            "n": 0,
            "false": 0,
            "paid": 0,
            "0": 0,
        }
        if pd.api.types.is_numeric_dtype(series):
            return (series.astype(float) > 0).astype(int)
        normalized = series.astype(str).str.strip().str.lower()
        return normalized.map(mapping).fillna(0).astype(int)

    def _build_models(self) -> dict[str, Any]:
        preprocessor = ColumnTransformer(
            transformers=[
                ("num", StandardScaler(), RISK_NUMERIC_FEATURES),
                ("cat", OneHotEncoder(handle_unknown="ignore"), RISK_CATEGORICAL_FEATURES),
            ]
        )
        models: dict[str, Any] = {
            "logistic_regression": Pipeline(
                steps=[
                    ("preprocessor", preprocessor),
                    (
                        "model",
                        LogisticRegression(
                            max_iter=500,
                            class_weight="balanced",
                            solver="lbfgs",
                            random_state=42,
                        ),
                    ),
                ]
            ),
            "random_forest": Pipeline(
                steps=[
                    ("preprocessor", preprocessor),
                    (
                        "model",
                        RandomForestClassifier(
                            n_estimators=250,
                            max_depth=10,
                            min_samples_leaf=2,
                            class_weight="balanced",
                            random_state=42,
                        ),
                    ),
                ]
            ),
        }
        try:
            from xgboost import XGBClassifier

            models["xgboost"] = Pipeline(
                steps=[
                    ("preprocessor", preprocessor),
                    (
                        "model",
                        XGBClassifier(
                            n_estimators=300,
                            max_depth=4,
                            learning_rate=0.05,
                            subsample=0.9,
                            colsample_bytree=0.9,
                            random_state=42,
                            eval_metric="logloss",
                        ),
                    ),
                ]
            )
        except Exception:
            pass
        return models

    def train(self, raw_df: pd.DataFrame, target_column: str | None = None) -> ModelArtifact:
        df = resolve_canonical_columns(raw_df)
        target_col = self._resolve_target_column(df, target_column)
        y = self._to_binary_target(df[target_col])

        features = prepare_risk_features(df)
        if len(features) < 20:
            raise ValueError("At least 20 records are required for model training.")
        if y.nunique() < 2:
            raise ValueError("Target column must contain both default and non-default samples.")

        stratify_target = y if y.value_counts().min() > 1 else None
        X_train, X_test, y_train, y_test = train_test_split(
            features,
            y,
            test_size=0.2,
            random_state=42,
            stratify=stratify_target,
        )

        all_metrics: dict[str, dict[str, float]] = {}
        best_model_name = ""
        best_model: Any = None
        best_auc = -1.0
        best_f1 = -1.0

        for model_name, model in self._build_models().items():
            model.fit(X_train, y_train)
            prob = model.predict_proba(X_test)[:, 1]
            pred = (prob >= 0.5).astype(int)

            try:
                auc = float(roc_auc_score(y_test, prob))
            except ValueError:
                auc = 0.0

            metrics = {
                "accuracy": float(accuracy_score(y_test, pred)),
                "precision": float(precision_score(y_test, pred, zero_division=0)),
                "recall": float(recall_score(y_test, pred, zero_division=0)),
                "f1": float(f1_score(y_test, pred, zero_division=0)),
                "roc_auc": auc,
            }
            all_metrics[model_name] = metrics

            if auc > best_auc or (abs(auc - best_auc) < 1e-6 and metrics["f1"] > best_f1):
                best_auc = auc
                best_f1 = metrics["f1"]
                best_model_name = model_name
                best_model = model

        self.model = best_model
        self.best_model_name = best_model_name
        self.metrics = all_metrics
        self.target_column = target_col
        self.trained_features = RISK_MODEL_FEATURES
        self.trained_at = datetime.now(timezone.utc).isoformat()
        self.save()

        return ModelArtifact(
            model=self.model,
            best_model_name=self.best_model_name,
            metrics=self.metrics,
            target_column=self.target_column,
            trained_features=self.trained_features,
            trained_at=self.trained_at,
        )

    def predict_default_probability(self, df: pd.DataFrame) -> np.ndarray:
        if self.model is None:
            raise RuntimeError("No trained model available.")
        prepared = prepare_risk_features(df)
        return self.model.predict_proba(prepared)[:, 1]


risk_model_manager = RiskModelManager(
    artifact_dir=settings.model_artifact_dir,
    filename=settings.risk_model_filename,
)

