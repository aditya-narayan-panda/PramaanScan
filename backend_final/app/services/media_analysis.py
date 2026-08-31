from __future__ import annotations

import json
import mimetypes
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np


# ============================================================
# PROJECT ROOT
# ============================================================
#
# This file lives at:
#   <repo_root>/backend_final/app/services/media_analysis.py
#
# The real ML packages (image_ml, audio, document,
# predict_multimodal.py, predict_video_v4.py, config.py) live
# one level deeper, inside <repo_root>/PramaanScan_ML/, not at
# the repo root itself. Only adding the repo root to sys.path
# means `import image_ml...` / `from audio.predictor import
# ...` / `from document.predictor import ...` / `from
# predict_multimodal import ...` all fail with
# ModuleNotFoundError, because those packages are not directly
# importable from the repo root. We add BOTH the repo root and
# the PramaanScan_ML directory so all ML modules resolve.

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ML_ROOT = PROJECT_ROOT / "PramaanScan_ML"

for _path in (PROJECT_ROOT, ML_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


# ============================================================
# HELPERS
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
    ".tif",
    ".tiff",
}

AUDIO_EXTENSIONS = {
    ".wav",
    ".mp3",
    ".flac",
    ".ogg",
    ".m4a",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".mov",
    ".avi",
    ".mkv",
    ".webm",
    ".m4v",
}

DOCUMENT_EXTENSIONS = {
    ".txt",
    ".pdf",
    ".doc",
    ".docx",
}


def _extension(filename: str) -> str:
    return Path(filename).suffix.lower()


def _modality_from_filename(
    filename: str,
    content_type: str = "",
) -> str:

    ext = _extension(filename)

    if ext in IMAGE_EXTENSIONS or content_type.startswith("image/"):
        return "IMAGE"

    if ext in AUDIO_EXTENSIONS or content_type.startswith("audio/"):
        return "AUDIO"

    if ext in VIDEO_EXTENSIONS or content_type.startswith("video/"):
        return "VIDEO"

    if (
        ext in DOCUMENT_EXTENSIONS
        or content_type.startswith("text/")
        or content_type == "application/pdf"
    ):
        return "DOCUMENT"

    return "UNKNOWN"


# ============================================================
# RISK MAPPING
# ============================================================

def _risk_label(
    score: float | None,
    verdict: str | None = None,
    inconclusive: bool = False,
) -> str:

    if inconclusive:
        return "INCONCLUSIVE"

    if score is None:
        return "INCONCLUSIVE"

    score = float(score)

    if verdict in {
        "FAKE",
        "Likely AI Generated",
        "SUSPICIOUS",
        "AI",
    }:
        if score >= 0.50:
            return "HIGH"

    if score >= 0.70:
        return "HIGH"

    if score >= 0.35:
        return "MEDIUM"

    return "LOW"


def _finalize_result(
    result: dict[str, Any],
    modality: str,
    model_name: str,
    risk_score: float | None,
    verdict: str | None = None,
    inconclusive: bool = False,
) -> dict[str, Any]:

    result["modality"] = modality
    result["risk_score"] = (
        round(float(risk_score), 6)
        if risk_score is not None
        else None
    )

    result["risk_label"] = _risk_label(
        risk_score,
        verdict=verdict,
        inconclusive=inconclusive,
    )

    result["model_name"] = model_name
    result["is_advisory"] = True

    result["evidence_type"] = (
        "AI-assisted manipulation-risk analysis"
    )

    result["disclaimer"] = (
        "This result is advisory secondary evidence and "
        "must be considered alongside cryptographic hash "
        "and provenance verification."
    )

    return result


# ============================================================
# IMAGE
# ============================================================

def analyze_image_bytes(
    data: bytes,
    filename: str,
) -> dict[str, Any]:

    if not data:
        raise ValueError("Image file is empty.")

    import cv2  # lazy import — cv2 only needed at call time
    from image_ml.services.prediction_service import predict_image

    buffer = np.frombuffer(
        data,
        dtype=np.uint8,
    )

    image_bgr = cv2.imdecode(
        buffer,
        cv2.IMREAD_COLOR,
    )

    if image_bgr is None:
        raise ValueError(
            "The uploaded file could not be decoded "
            "as a valid image."
        )

    image_rgb = cv2.cvtColor(
        image_bgr,
        cv2.COLOR_BGR2RGB,
    )

    prediction = predict_image(
        image_array=image_rgb,
        filename=filename,
    )

    if hasattr(prediction, "model_dump"):
        result = prediction.model_dump()
    else:
        result = prediction.dict()

    score = result.get(
        "overall_probability"
    )

    verdict = result.get("verdict")

    return _finalize_result(
        result=result,
        modality="IMAGE",
        model_name=(
            "SVM + Random Forest + "
            "Logistic Regression"
        ),
        risk_score=score,
        verdict=verdict,
        inconclusive=result.get(
            "is_inconclusive",
            False,
        ),
    )


# ============================================================
# AUDIO
# ============================================================

def analyze_audio_bytes(
    data: bytes,
    filename: str,
) -> dict[str, Any]:

    if not data:
        raise ValueError("Audio file is empty.")

    from audio.predictor import predict_audio

    suffix = _extension(filename) or ".wav"

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False,
    ) as tmp:

        temp_path = Path(tmp.name)
        tmp.write(data)

    try:

        result = predict_audio(
            str(temp_path)
        )

    finally:

        try:
            temp_path.unlink()
        except OSError:
            pass

    score = float(
        result["average_ai_score"]
    )

    verdict = result.get(
        "final_prediction",
        "Human",
    )

    output = {
        "filename": filename,
        "models": result.get("models", {}),
        "average_ai_score": score,
        "average_human_score": result.get(
            "average_human_score"
        ),
        "ai_votes": result.get(
            "ai_votes"
        ),
        "total_models": result.get(
            "total_models"
        ),
        "final_prediction": verdict,
    }

    return _finalize_result(
        result=output,
        modality="AUDIO",
        model_name=(
            "Audio SVM + Random Forest + "
            "Logistic Regression"
        ),
        risk_score=score,
        verdict=verdict,
    )


# ============================================================
# VIDEO
# ============================================================

def analyze_video_bytes(
    data: bytes,
    filename: str,
) -> dict[str, Any]:

    if not data:
        raise ValueError("Video file is empty.")

    from predict_multimodal import (
        analyze_video_component,
        analyze_audio,
        fuse_results,
        check_ffmpeg,
    )

    if not check_ffmpeg():
        raise RuntimeError(
            "FFmpeg was not found in PATH."
        )

    suffix = _extension(filename) or ".mp4"

    with tempfile.NamedTemporaryFile(
        suffix=suffix,
        delete=False,
    ) as tmp:

        temp_path = Path(tmp.name)
        tmp.write(data)

    try:

        video_result = analyze_video_component(
            temp_path
        )

        audio_result = analyze_audio(
            temp_path
        )

        fusion_result = fuse_results(
            video_result,
            audio_result,
        )

    finally:

        try:
            temp_path.unlink()
        except OSError:
            pass

    score = float(
        fusion_result["multimodal_score"]
    )

    verdict = fusion_result.get(
        "final_verdict",
        "UNCERTAIN",
    )

    inconclusive = (
        verdict == "UNCERTAIN"
    )

    output = {
        "filename": filename,
        "media_type": "video",

        "video": video_result,

        "audio": audio_result,

        "multimodal": fusion_result,
    }

    return _finalize_result(
        result=output,
        modality="VIDEO",
        model_name=(
            "DIVERSE_400 + Audio Ensemble "
            "Multimodal Fusion"
        ),
        risk_score=score,
        verdict=verdict,
        inconclusive=inconclusive,
    )


# ============================================================
# DOCUMENT / TEXT
# ============================================================

def analyze_document_bytes(
    data: bytes,
    filename: str,
    content_type: str = "",
) -> dict[str, Any]:

    if not data:
        raise ValueError(
            "Document file is empty."
        )

    from document.predictor import (
        analyze_document,
    )

    result = analyze_document(
        data=data,
        filename=filename,
        content_type=content_type,
    )

    model_result = result.get(
        "model",
        {}
    )

    probabilities = model_result.get(
        "probabilities",
        {}
    )

    prediction = model_result.get(
        "prediction"
    )

    # Try to extract suspicious probability.
    score = None

    for key, value in probabilities.items():

        normalized = str(key).upper()

        if (
            "SUSPICIOUS" in normalized
            or "FAKE" in normalized
        ):
            score = float(value) / 100.0
            break

    if score is None:

        confidence = model_result.get(
            "confidence_percent"
        )

        if prediction == "SUSPICIOUS":
            score = (
                float(confidence or 100.0)
                / 100.0
            )
        else:
            score = 0.0

    verdict = result.get(
        "final_verdict",
        prediction,
    )

    return _finalize_result(
        result=result,
        modality="DOCUMENT",
        model_name=(
            "Document Verification ML + "
            "Forensics"
        ),
        risk_score=score,
        verdict=verdict,
    )


# ============================================================
# UNIFIED ENTRY POINT
# ============================================================

def analyze_media_bytes(
    data: bytes,
    filename: str,
    content_type: str = "",
) -> dict[str, Any]:

    modality = _modality_from_filename(
        filename,
        content_type,
    )

    if modality == "IMAGE":

        return analyze_image_bytes(
            data,
            filename,
        )

    if modality == "AUDIO":

        return analyze_audio_bytes(
            data,
            filename,
        )

    if modality == "VIDEO":

        return analyze_video_bytes(
            data,
            filename,
        )

    if modality == "DOCUMENT":

        return analyze_document_bytes(
            data,
            filename,
            content_type,
        )

    return {
        "filename": filename,
        "modality": "UNKNOWN",
        "available": False,
        "risk_score": None,
        "risk_label": "INCONCLUSIVE",
        "is_advisory": True,
        "reason": (
            "Unsupported media type."
        ),
    }
