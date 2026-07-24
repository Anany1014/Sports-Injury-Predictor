"""
model.src.utils.config
~~~~~~~~~~~~~~~~~~~~~~~
Load and validate YAML configuration files using Pydantic.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# ---------------------------------------------------------------------------
# Pydantic settings (reads from .env)
# ---------------------------------------------------------------------------
class EnvSettings(BaseSettings):
    """Runtime settings sourced from environment variables / .env file."""

    app_env: str = Field("development", alias="APP_ENV")
    data_raw_dir: Path = Field(Path("data/raw"), alias="DATA_RAW_DIR")
    data_processed_dir: Path = Field(Path("data/processed"), alias="DATA_PROCESSED_DIR")
    artifacts_dir: Path = Field(Path("model/artifacts"), alias="ARTIFACTS_DIR")
    mlflow_tracking_uri: str = Field("mlruns", alias="MLFLOW_TRACKING_URI")
    mlflow_experiment_name: str = Field(
        "sports-injury-predictor", alias="MLFLOW_EXPERIMENT_NAME"
    )

    model_config = {"env_file": ".env", "populate_by_name": True}


# ---------------------------------------------------------------------------
# YAML loader
# ---------------------------------------------------------------------------
def load_yaml_config(config_path: str | Path) -> dict[str, Any]:
    """Load a YAML config file and return it as a plain dict."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with path.open() as f:
        return yaml.safe_load(f)


# Singleton instances
env = EnvSettings()
training_cfg: dict[str, Any] = load_yaml_config(
    Path(__file__).parents[2] / "configs" / "training_config.yaml"
)
