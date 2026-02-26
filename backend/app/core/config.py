from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FinAware AI API"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    model_artifact_dir: str = "artifacts"
    risk_model_filename: str = "risk_model.joblib"
    default_target_column: str = "defaulted"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def validate_cors_origins(cls, value: Any) -> Any:
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value


settings = Settings()

