"""
Praman Scan - Model loader.

Loads the trained SVM, Random Forest, Logistic Regression models, the
feature scaler, and the label encoder from disk exactly once (singleton
pattern) and keeps them resident in memory for the lifetime of the
process, so that repeated API calls do not pay the cost of unpickling on
every request.
"""
import json
import threading
from pathlib import Path
from typing import Optional

import joblib

from image_ml.config import get_settings
from image_ml.utils.logger import get_logger

logger = get_logger(__name__)


class ModelNotTrainedError(Exception):
    """Raised when saved model artifacts are missing from disk."""


class ModelBundle:
    """Holds all artifacts required to run inference."""

    def __init__(self):
        self.svm = None
        self.random_forest = None
        self.logistic = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names: Optional[list] = None
        self.metadata: dict = {}
        self.loaded: bool = False


class ModelLoader:
    _instance: Optional["ModelLoader"] = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._bundle = ModelBundle()
        return cls._instance

    @property
    def bundle(self) -> ModelBundle:
        if not self._bundle.loaded:
            self.load()
        return self._bundle

    def load(self, force: bool = False) -> ModelBundle:
        if self._bundle.loaded and not force:
            return self._bundle

        settings = get_settings()
        model_dir: Path = settings.MODEL_DIR

        required = {
            "svm": model_dir / settings.SVM_MODEL_FILE,
            "random_forest": model_dir / settings.RF_MODEL_FILE,
            "logistic": model_dir / settings.LOGISTIC_MODEL_FILE,
            "scaler": model_dir / settings.SCALER_FILE,
            "label_encoder": model_dir / settings.LABEL_ENCODER_FILE,
        }

        missing = [name for name, path in required.items() if not path.exists()]
        if missing:
            raise ModelNotTrainedError(
                "The following trained model artifacts are missing: "
                f"{', '.join(missing)}. Run `python train/train.py` first, "
                f"pointing DATASET_DIR at a populated dataset."
            )

        logger.info("Loading model artifacts from %s", model_dir)
        self._bundle.svm = joblib.load(required["svm"])
        self._bundle.random_forest = joblib.load(required["random_forest"])
        self._bundle.logistic = joblib.load(required["logistic"])
        self._bundle.scaler = joblib.load(required["scaler"])
        self._bundle.label_encoder = joblib.load(required["label_encoder"])

        metadata_path = model_dir / settings.METADATA_FILE
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                self._bundle.metadata = json.load(f)
            self._bundle.feature_names = self._bundle.metadata.get("feature_names")

        self._bundle.loaded = True
        logger.info("Model artifacts loaded successfully.")
        return self._bundle


def get_model_bundle() -> ModelBundle:
    return ModelLoader().bundle
