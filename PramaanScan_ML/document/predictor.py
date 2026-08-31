from __future__ import annotations

from pathlib import Path
from typing import Optional

import joblib

from .text_extraction import extract_content
from .forensics import (
    standalone_forensics,
    compare_reference,
)


# ============================================================
# PATHS
# ============================================================

DOCUMENT_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    DOCUMENT_DIR
    / "verification_model.joblib"
)


# ============================================================
# SAFETY CHECK
# ============================================================

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"Document verification model not found:\n"
        f"{MODEL_PATH}"
    )


# ============================================================
# LOAD MODEL
# ============================================================

verification_model = joblib.load(
    MODEL_PATH
)


# ============================================================
# MODEL INFORMATION
# ============================================================

EXPECTED_CLASSES = getattr(
    verification_model,
    "classes_",
    None
)


# ============================================================
# TEXT MODEL PREDICTION
# ============================================================

def predict_text(text: str) -> dict:

    if not isinstance(text, str):
        raise TypeError(
            "text must be a string"
        )

    if not text.strip():
        raise ValueError(
            "No readable text was extracted from the document."
        )

    # --------------------------------------------------------
    # Prediction
    # --------------------------------------------------------

    prediction = verification_model.predict(
        [text]
    )[0]

    # --------------------------------------------------------
    # Probability
    # --------------------------------------------------------

    probabilities = verification_model.predict_proba(
        [text]
    )[0]

    classes = list(
        verification_model.classes_
    )

    probability_map = {
        str(label): float(probability)
        for label, probability
        in zip(classes, probabilities)
    }

    # --------------------------------------------------------
    # Confidence
    # --------------------------------------------------------

    confidence = max(
        probability_map.values()
    )

    return {
        "prediction": str(prediction),

        "confidence_percent": round(
            confidence * 100,
            2
        ),

        "probabilities": {
            label: round(
                probability * 100,
                2
            )
            for label, probability
            in probability_map.items()
        }
    }


# ============================================================
# DOCUMENT ANALYSIS
# ============================================================

def analyze_document(
    data: bytes,
    filename: str,
    content_type: str = "",
    reference_data: Optional[bytes] = None,
) -> dict:

    # ========================================================
    # EXTRACT TEXT
    # ========================================================

    extracted = extract_content(
        data,
        filename,
        content_type
    )

    text = extracted["text"]

    # ========================================================
    # ML VERIFICATION
    # ========================================================

    model_result = predict_text(
        text
    )

    # ========================================================
    # FORENSICS
    # ========================================================

    if (
        extracted["file_type"] == "PDF"
        and reference_data is not None
    ):

        forensic_result = compare_reference(
            reference_data,
            data
        )

    elif extracted["file_type"] == "PDF":

        forensic_result = standalone_forensics(
            data
        )

    else:

        forensic_result = {
            "mode": "TEXT_FORENSICS",
            "assessment": "NOT_AVAILABLE",
            "tamper_risk": "INCONCLUSIVE",
            "confidence_percent": 50.0,
            "evidence": [],
            "note": (
                "PDF structural forensics are not "
                "available for TXT files."
            )
        }

    # ========================================================
    # FINAL ASSESSMENT
    # ========================================================

    prediction = model_result[
        "prediction"
    ]

    confidence = model_result[
        "confidence_percent"
    ]

    # --------------------------------------------------------
    # Base result from ML model
    # --------------------------------------------------------

    if prediction == "SUSPICIOUS":

        final_verdict = "SUSPICIOUS"

    else:

        final_verdict = "OFFICIAL"

    # --------------------------------------------------------
    # Reference forensics can provide additional evidence.
    #
    # Do NOT automatically call a completely different
    # document "tampered". compare_reference() already
    # distinguishes REFERENCE_MISMATCH.
    # --------------------------------------------------------

    if (
        forensic_result.get("assessment")
        == "SUSPICIOUS"
    ):

        final_verdict = "SUSPICIOUS"

    # ========================================================
    # RETURN RESULT
    # ========================================================

    return {

        "filename":
            filename,

        "file_type":
            extracted["file_type"],

        "document": {

            "pages":
                extracted["pages"],

            "characters_extracted":
                extracted["characters_extracted"],

            "words_extracted":
                extracted["words_extracted"]
        },

        "model": {

            "prediction":
                prediction,

            "confidence_percent":
                confidence,

            "probabilities":
                model_result["probabilities"]
        },

        "forensics":
            forensic_result,

        "final_verdict":
            final_verdict
    }


# ============================================================
# STANDALONE FILE TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 70)
    print("PRAMAANSCAN DOCUMENT MODEL")
    print("=" * 70)

    print()
    print("Document directory:")
    print(DOCUMENT_DIR)

    print()
    print("Model:")
    print(MODEL_PATH)

    print()
    print("Model type:")
    print(type(verification_model).__name__)

    print()
    print("Classes:")

    if EXPECTED_CLASSES is not None:

        for label in EXPECTED_CLASSES:
            print(
                f"  - {label}"
            )

    else:

        print("  Unknown")

    print()
    print("Document predictor ready.")