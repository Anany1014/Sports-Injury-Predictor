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
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    model_config = {"env_file": ".env", "populate_by_name": True}


settings = Settings()
