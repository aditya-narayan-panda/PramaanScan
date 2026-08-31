"""
Praman Scan - Prediction service.

Implements the full inference pipeline described in the project brief:

    Upload Image
        -> Feature Extraction
        -> Feature Scaling
        -> Three ML Models (SVM, Random Forest, Logistic Regression)
        -> Soft Voting (average of the three probabilities)
        -> Verdict (Authentic / Likely AI Generated / Inconclusive)
        -> JSON response
"""
import time
from collections import defaultdict
from typing import List

import numpy as np

from image_ml.config import get_settings
from image_ml.schemas.prediction import (
    ModelPrediction,
    PredictionResponse,
    FeatureImportanceItem,
)
from image_ml.services.feature_extraction import extract_feature_vector
from image_ml.services.model_loader import get_model_bundle
from image_ml.utils.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()


def _group_name(feature_name: str) -> str:
    """Map a raw feature column name to a human-readable group used for the
    feature-importance breakdown shown on the result page."""
    prefix_map = {
        "lbp_": "Local Binary Pattern (Texture)",
        "hog_": "Histogram of Oriented Gradients (Shape)",
        "color_": "Color Histogram",
        "glcm_": "Texture Statistics (GLCM)",
        "fft_": "Frequency Domain (FFT)",
        "edge_": "Edge Density",
        "sharpness_": "Sharpness",
        "noise_": "Noise Statistics",
        "compression_": "Compression Statistics",
    }
    for prefix, label in prefix_map.items():
        if feature_name.startswith(prefix):
            return label
    return "Other"


def _compute_feature_importance() -> List[FeatureImportanceItem]:
    """Derive a grouped feature-importance breakdown from the Random Forest's
    native `feature_importances_`, since RF is the only one of the three
    models that exposes per-feature importances directly."""
    bundle = get_model_bundle()
    rf = bundle.random_forest
    names = bundle.feature_names

    if rf is None or names is None or not hasattr(rf, "feature_importances_"):
        return []

    importances = rf.feature_importances_
    if len(importances) != len(names):
        return []

    grouped = defaultdict(float)
    for name, importance in zip(names, importances):
        grouped[_group_name(name)] += float(importance)

    total = sum(grouped.values()) or 1.0
    items = [
        FeatureImportanceItem(feature_group=group, importance=round(value / total, 4))
        for group, value in sorted(grouped.items(), key=lambda kv: kv[1], reverse=True)
    ]
    return items


def _determine_verdict(mean_prob: float, std_prob: float) -> tuple:
    """
    Returns (verdict, confidence, is_inconclusive) following the rules in
    the brief: if the three models disagree heavily (std above threshold),
    always return "Inconclusive" rather than a falsely confident verdict.
    """
    if std_prob > settings.DISAGREEMENT_STD_THRESHOLD:
        return "Inconclusive", "N/A", True

    margin = abs(mean_prob - 0.5)
    if margin >= settings.HIGH_CONFIDENCE_MARGIN:
        confidence = "High"
    elif margin >= settings.MEDIUM_CONFIDENCE_MARGIN:
        confidence = "Medium"
    else:
        confidence = "Low"

    verdict = "Likely AI Generated" if mean_prob >= settings.AI_THRESHOLD else "Authentic"
    return verdict, confidence, False


def predict_image(image_array: np.ndarray, filename: str) -> PredictionResponse:
    start = time.perf_counter()

    bundle = get_model_bundle()

    feature_vector = extract_feature_vector(image_array)
    x = feature_vector.values.reshape(1, -1)
    x_scaled = bundle.scaler.transform(x)

    # Each classifier's classes_ ordering may differ; always read the
    # probability associated with the "fake" / "ai_generated" label via the
    # label encoder to be safe.
    ai_label_index = _resolve_ai_class_index(bundle)

    svm_prob = float(bundle.svm.predict_proba(x_scaled)[0][ai_label_index])
    rf_prob = float(bundle.random_forest.predict_proba(x_scaled)[0][ai_label_index])
    logistic_prob = float(bundle.logistic.predict_proba(x_scaled)[0][ai_label_index])

    probs = np.array([svm_prob, rf_prob, logistic_prob])

    # Use the validated weights computed during training (from each
    # model's measured ROC AUC on the held-out test set) if available,
    # falling back to a plain equal-weight average otherwise - e.g. for
    # models trained before this weighting feature existed.
    weight_order = ["svm", "random_forest", "logistic"]
    weights_dict = bundle.metadata.get("ensemble_weights") or {}
    if weights_dict and all(k in weights_dict for k in weight_order):
        weights = np.array([weights_dict[k] for k in weight_order])
    else:
        weights = np.array([1 / 3, 1 / 3, 1 / 3])

    mean_prob = float(np.average(probs, weights=weights))
    # Disagreement is still measured on the RAW, unweighted probabilities -
    # this keeps the "Inconclusive when models disagree" safeguard honest
    # and independent of how much weight any one model happens to carry.
    std_prob = float(probs.std())
    agreement_score = float(max(0.0, 1.0 - (std_prob / 0.5)))  # normalise: std of 0.5 => 0 agreement

    verdict, confidence, is_inconclusive = _determine_verdict(mean_prob, std_prob)

    individual = [
        ModelPrediction(model_name="Support Vector Machine", probability_ai_generated=round(svm_prob, 4)),
        ModelPrediction(model_name="Random Forest", probability_ai_generated=round(rf_prob, 4)),
        ModelPrediction(model_name="Logistic Regression", probability_ai_generated=round(logistic_prob, 4)),
    ]

    feature_importance = _compute_feature_importance()

    elapsed_ms = (time.perf_counter() - start) * 1000.0

    response = PredictionResponse(
        filename=filename,
        overall_probability=round(mean_prob, 4),
        verdict=verdict,
        confidence=confidence,
        model_agreement_score=round(agreement_score, 4),
        disagreement_std=round(std_prob, 4),
        is_inconclusive=is_inconclusive,
        individual_predictions=individual,
        feature_importance=feature_importance,
        processing_time_ms=round(elapsed_ms, 2),
    )

    logger.info(
        "Prediction for '%s': verdict=%s mean=%.4f std=%.4f (%.2f ms)",
        filename, verdict, mean_prob, std_prob, elapsed_ms,
    )
    return response


def _resolve_ai_class_index(bundle) -> int:
    """
    The label encoder maps class strings ('real' / 'fake') to integers.
    Each sklearn classifier's predict_proba columns follow `classes_`,
    which is populated from the encoded integer labels seen during
    training and is not guaranteed to put the positive ("fake"/AI) class
    at index 1. This resolves the correct column for all three models
    (they are trained on the same encoded labels, so the index is shared).
    """
    try:
        ai_encoded_label = bundle.label_encoder.transform(["fake"])[0]
    except Exception:
        # Fallback: assume standard alphabetical encoding where
        # 'fake' < 'real', i.e. index 0. If encoder classes differ,
        # default to the last column.
        return 0
    classes = list(bundle.random_forest.classes_)
    try:
        return classes.index(ai_encoded_label)
    except ValueError:
        return len(classes) - 1