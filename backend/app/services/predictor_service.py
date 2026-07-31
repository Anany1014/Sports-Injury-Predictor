import os
import json
import logging
import pandas as pd

from backend.app.core.config import settings
from backend.app.core.privacy import pseudonymizer, biometric_encryptor
from backend.app.schemas.prediction import AthleteRecord, PredictionResponse
from model.src.models.predict import InjuryPredictor

MODEL_VERSION = "1.0.0"
logger = logging.getLogger(__name__)


class PredictorService:
    """Singleton service that holds the loaded ML model."""

    def __init__(self) -> None:
        self._predictor = InjuryPredictor(artifacts_dir=settings.artifacts_dir)

    def load(self) -> None:
        self._predictor.load()

    def _get_top_factors(self, record_dict: dict) -> list[str]:
        factors = []

        # Sport and Position biomechanical factor
        sport = str(record_dict.get("sport", "")).strip()
        position = str(record_dict.get("position", "")).strip()
        
        high_risk_positions = ["Fast Bowler", "Pitcher", "Prop", "Hooker", "Forward", "Midfielder", "Marathoner"]
        if any(hrp.lower() in position.lower() for hrp in high_risk_positions):
            factors.append(f"High-Impact Sport Position ({position} in {sport})")

        # Intensity factor
        intensity = record_dict.get("weekly_intensity_score", 0)
        if intensity >= 7.5:
            factors.append(f"High Weekly Intensity ({intensity:.1f}/10)")
        elif intensity >= 5.0:
            factors.append(f"Moderate Training Exertion ({intensity:.1f}/10)")

        # Volume factor
        volume = record_dict.get("weekly_volume_hrs", 0)
        if volume >= 14.0:
            factors.append(f"Elevated Weekly Volume ({volume:.1f} hrs)")

        # Recovery factors
        sleep = record_dict.get("sleep_hours", 8)
        if sleep < 7.0:
            factors.append(f"Sleep Deficit ({sleep:.1f} hrs/night)")

        soreness = record_dict.get("soreness_score", 0)
        if soreness >= 5.0:
            factors.append(f"High Muscle Soreness ({soreness:.1f}/10)")

        rest = record_dict.get("rest_days", 2)
        if rest <= 1:
            factors.append(f"Insufficient Rest ({rest} rest days)")

        # Injury history
        priors = record_dict.get("prior_injuries", 0)
        days_since = record_dict.get("days_since_last_injury", 365)
        if priors > 0 and days_since < 90:
            factors.append(f"Recent Injury History ({priors} prior, {int(days_since)}d ago)")

        if not factors:
            factors = ["Workload within safe threshold", "Normal recovery baseline"]

        return factors[:3]

    def _save_to_secure_audit_log(self, record: AthleteRecord, risk_label: str) -> None:
        """Securely logs the prediction event with pseudonymized IDs and encrypted health metrics."""
        # 1. Pseudonymize the athlete ID
        pseudo_id = pseudonymizer.pseudonymize(record.athlete_id)

        # 2. Extract and encrypt sensitive metrics (HIPAA/GDPR Compliance)
        sensitive_data = {
            "age": record.age,
            "weight_kg": record.weight_kg,
            "height_cm": record.height_cm,
            "weekly_volume_hrs": record.weekly_volume_hrs,
            "weekly_intensity_score": record.weekly_intensity_score,
            "sleep_hours": record.sleep_hours,
            "hrv_ms": record.hrv_ms,
            "soreness_score": record.soreness_score,
            "rest_days": record.rest_days,
            "prior_injuries": record.prior_injuries,
            "days_since_last_injury": record.days_since_last_injury,
            "sport": record.sport,
            "position": record.position
        }
        encrypted_metrics = biometric_encryptor.encrypt_data(sensitive_data)

        # 3. Log securely without exposing PHI
        logger.info(f"AUDIT LOG: Secure prediction requested for {pseudo_id} with injury risk: {risk_label}")

        # 4. Save to disk to satisfy 'at-rest' requirement
        audit_file_path = os.path.join(settings.artifacts_dir, "secure_predictions_audit.json")
        audit_record = {
            "timestamp": record.date,
            "athlete_pseudonym": pseudo_id,
            "encrypted_biometrics": encrypted_metrics,
            "injury_risk_label": risk_label
        }

        try:
            records = []
            if os.path.exists(audit_file_path):
                with open(audit_file_path, "r", encoding="utf-8") as f:
                    try:
                        records = json.load(f)
                    except json.JSONDecodeError:
                        pass
            records.append(audit_record)
            with open(audit_file_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write secure audit log: {e}")

    def predict_one(self, record: AthleteRecord) -> PredictionResponse:
        record_dict = record.model_dump()
        result = self._predictor.predict_single(record_dict)
        factors = self._get_top_factors(record_dict)

        # Persist secure audit log (HIPAA compliant)
        self._save_to_secure_audit_log(record, result["injury_risk_label"])

        return PredictionResponse(
            athlete_id=record.athlete_id,
            injury_probability=result["injury_probability"],
            injury_risk_label=result["injury_risk_label"],
            top_contributing_factors=factors,
            model_version=MODEL_VERSION,
        )

    def predict_batch(self, records: list[AthleteRecord]) -> list[PredictionResponse]:
        df = pd.DataFrame([r.model_dump() for r in records])
        result_df = self._predictor.predict(df)
        responses = []
        for i, record in enumerate(records):
            record_dict = record.model_dump()
            factors = self._get_top_factors(record_dict)
            risk_label = str(result_df["injury_risk_label"].iloc[i])

            # Persist secure audit log (HIPAA compliant)
            self._save_to_secure_audit_log(record, risk_label)

            responses.append(
                PredictionResponse(
                    athlete_id=record.athlete_id,
                    injury_probability=float(result_df["injury_probability"].iloc[i]),
                    injury_risk_label=risk_label,
                    top_contributing_factors=factors,
                    model_version=MODEL_VERSION,
                )
            )
        return responses

