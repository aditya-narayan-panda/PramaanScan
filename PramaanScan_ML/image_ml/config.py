"""
Praman Scan - Backend Configuration
Centralised configuration loaded from environment variables.
No hardcoded paths anywhere else in the codebase should exist; everything
that varies between environments (paths, thresholds, CORS origins) is
defined here and driven by a .env file.
"""
import os
from pathlib import Path
from functools import lru_cache

from dotenv import load_dotenv

# Load .env from the backend root directory (if present).
BACKEND_ROOT = Path(__file__).resolve().parent
load_dotenv(BACKEND_ROOT / ".env")


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _get_float(name: str, default: float) -> float:
    val = os.getenv(name)
    if val is None or val == "":
        return default
    try:
        return float(val)
    except ValueError:
        return default


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


class Settings:
    """Application settings. Instantiated once via get_settings()."""

    # --- General ---
    APP_NAME: str = os.getenv("APP_NAME", "Praman Scan")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # --- CORS ---
    CORS_ORIGINS: list = [
        origin.strip()
        for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if origin.strip()
    ]

    # --- Paths (all resolved relative to BACKEND_ROOT unless absolute) ---
    BACKEND_ROOT: Path = BACKEND_ROOT
    DATASET_DIR: Path = Path(os.getenv("DATASET_DIR", str(BACKEND_ROOT / "dataset")))
    MODEL_DIR: Path = Path(os.getenv("MODEL_DIR", str(BACKEND_ROOT / "saved_models")))
    UPLOAD_TMP_DIR: Path = Path(os.getenv("UPLOAD_TMP_DIR", str(BACKEND_ROOT / "tmp_uploads")))
    LOG_DIR: Path = Path(os.getenv("LOG_DIR", str(BACKEND_ROOT / "logs")))

    # --- Model file names ---
    SVM_MODEL_FILE: str = os.getenv("SVM_MODEL_FILE", "svm.pkl")
    RF_MODEL_FILE: str = os.getenv("RF_MODEL_FILE", "random_forest.pkl")
    LOGISTIC_MODEL_FILE: str = os.getenv("LOGISTIC_MODEL_FILE", "logistic.pkl")
    SCALER_FILE: str = os.getenv("SCALER_FILE", "feature_scaler.pkl")
    LABEL_ENCODER_FILE: str = os.getenv("LABEL_ENCODER_FILE", "label_encoder.pkl")
    METADATA_FILE: str = os.getenv("METADATA_FILE", "training_metadata.json")

    # --- Inference thresholds ---
    # Above this probability => "Likely AI Generated"
    AI_THRESHOLD: float = _get_float("AI_THRESHOLD", 0.5)
    # If the standard deviation between the three model probabilities exceeds
    # this value, the verdict is downgraded to "Inconclusive" regardless of
    # the average probability, to avoid false confidence.
    DISAGREEMENT_STD_THRESHOLD: float = _get_float("DISAGREEMENT_STD_THRESHOLD", 0.25)
    # Confidence bands, based on distance of the average probability from 0.5
    HIGH_CONFIDENCE_MARGIN: float = _get_float("HIGH_CONFIDENCE_MARGIN", 0.35)
    MEDIUM_CONFIDENCE_MARGIN: float = _get_float("MEDIUM_CONFIDENCE_MARGIN", 0.15)

    # --- Upload constraints ---
    MAX_UPLOAD_SIZE_MB: int = _get_int("MAX_UPLOAD_SIZE_MB", 15)
    ALLOWED_EXTENSIONS: tuple = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

    # --- Feature extraction params ---
    IMAGE_RESIZE_DIM: int = _get_int("IMAGE_RESIZE_DIM", 256)
    LBP_RADIUS: int = _get_int("LBP_RADIUS", 2)
    LBP_POINTS: int = _get_int("LBP_POINTS", 16)
    HOG_PIXELS_PER_CELL: int = _get_int("HOG_PIXELS_PER_CELL", 16)
    HOG_CELLS_PER_BLOCK: int = _get_int("HOG_CELLS_PER_BLOCK", 2)
    COLOR_HIST_BINS: int = _get_int("COLOR_HIST_BINS", 32)

    # --- Training params ---
    RANDOM_STATE: int = _get_int("RANDOM_STATE", 42)
    TEST_SIZE: float = _get_float("TEST_SIZE", 0.2)
    SVM_KERNEL: str = os.getenv("SVM_KERNEL", "rbf")
    SVM_C: float = _get_float("SVM_C", 2.0)
    RF_N_ESTIMATORS: int = _get_int("RF_N_ESTIMATORS", 300)
    RF_MAX_DEPTH: int = _get_int("RF_MAX_DEPTH", 18)
    LOGISTIC_MAX_ITER: int = _get_int("LOGISTIC_MAX_ITER", 2000)

    # --- Hyperparameter tuning (GridSearchCV over each model's param grid,
    # defined in models/ml_models.py, scored via cross-validation) ---
    ENABLE_HYPERPARAMETER_TUNING: bool = _get_bool("ENABLE_HYPERPARAMETER_TUNING", True)
    TUNING_CV_FOLDS: int = _get_int("TUNING_CV_FOLDS", 5)
    TUNING_SCORING: str = os.getenv("TUNING_SCORING", "roc_auc")

    # --- Probability calibration (CalibratedClassifierCV) ---
    # Applied to SVM and Logistic Regression only; Random Forest's
    # probabilities are already reasonably well-calibrated by nature of
    # averaging many trees' votes.
    ENABLE_PROBABILITY_CALIBRATION: bool = _get_bool("ENABLE_PROBABILITY_CALIBRATION", True)
    # 'sigmoid' (Platt scaling) is safer for smaller datasets; 'isotonic'
    # needs more data per class to avoid overfitting the calibration curve.
    CALIBRATION_METHOD: str = os.getenv("CALIBRATION_METHOD", "sigmoid")
    CALIBRATION_CV_FOLDS: int = _get_int("CALIBRATION_CV_FOLDS", 5)

    # --- Validated ensemble weighting ---
    # If enabled, the ensemble's final probability is a weighted average of
    # the three models, with weights derived from each model's measured
    # ROC AUC on the held-out test set (not a guessed/hardcoded number).
    # If disabled, or if any model's AUC is unavailable, falls back to a
    # plain equal-weight average (matches the original soft-voting design).
    ENABLE_VALIDATED_WEIGHTING: bool = _get_bool("ENABLE_VALIDATED_WEIGHTING", True)

    def ensure_directories(self) -> None:
        for path in (self.MODEL_DIR, self.UPLOAD_TMP_DIR, self.LOG_DIR):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_directories()
    return settings