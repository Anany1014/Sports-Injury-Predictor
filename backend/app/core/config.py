"""
backend.app.core.config
~~~~~~~~~~~~~~~~~~~~~~~~
Application-level settings sourced from environment variables.
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = Field("development", alias="APP_ENV")
    api_host: str = Field("0.0.0.0", alias="API_HOST")
    api_port: int = Field(8000, alias="API_PORT")
    artifacts_dir: Path = Field(Path("model/artifacts"), alias="ARTIFACTS_DIR")
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

    # Security configuration
    secret_key: str = Field("change-me-in-production", alias="SECRET_KEY")
    jwt_secret_key: str = Field("jwt-secret-key-change-me-in-production-1234567890", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    # 32-byte base64 key for AES-256 GCM encryption (default decodes to 'test_key_test_key_test_key_test_key')
    encryption_key: str = Field("dGVzdF9rZXlfdGVzdF9rZXlfdGVzdF9rZXlfdGVzdF9rZXk=", alias="ENCRYPTION_KEY")
    
    # Rate Limiting
    prediction_rate_limit: str = Field("100/minute", alias="PREDICTION_RATE_LIMIT")

    # OpenRouter LLM Configuration
    openrouter_api_key: str = Field("", alias="OPENROUTER_API_KEY")
    openrouter_model: str = Field("nvidia/nemotron-nano-9b-v2:free", alias="OPENROUTER_MODEL")

    model_config = {"env_file": ".env", "populate_by_name": True, "extra": "ignore"}


settings = Settings()

