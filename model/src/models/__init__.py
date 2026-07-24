"""model.src.models package."""
from model.src.models.predict import InjuryPredictor
from model.src.models.two_stage_cascade import TwoStageCascadeClassifier

try:
    from model.src.models.train import train
    __all__ = ["InjuryPredictor", "TwoStageCascadeClassifier", "train"]
except ModuleNotFoundError:
    __all__ = ["InjuryPredictor", "TwoStageCascadeClassifier"]
