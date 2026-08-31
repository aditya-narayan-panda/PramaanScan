from pathlib import Path
import sys
import numpy as np
import tensorflow as tf

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)


# ============================================================
# PATH
# ============================================================

ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ============================================================
# PROJECT IMPORTS
# ============================================================

from config import *
from src.dataset import read_manifest, VideoSequence
from src.face import MediaPipeFaceDetector

# IMPORTANT:
# Import custom Keras layer before loading the saved model.
from src.model import TemporalPositionEmbedding


# ============================================================
# DIVERSE MODEL PATH
# ============================================================

DIVERSE_MODEL_PATH = (
    ROOT
    / "outputs"
    / "models"
    / "DIVERSE_400.keras"
)


# ============================================================
# CHECK MODEL
# ============================================================

if not DIVERSE_MODEL_PATH.exists():

    raise SystemExit(
        "\nDiverse model not found:\n"
        f"{DIVERSE_MODEL_PATH}\n\n"
        "Make sure train_diverse.py completed successfully."
    )


# ============================================================
# LOAD TEST DATA
# ============================================================

test = read_manifest(TEST_MANIFEST)


print("=" * 70)
print("PRAMAANSCAN DIVERSE MODEL TEST EVALUATION")
print("=" * 70)

print()
print("Test videos :", len(test))
print("Model       :", DIVERSE_MODEL_PATH)


# ============================================================
# FACE DETECTOR
# ============================================================

print()
print("Initializing face detector...")

det = MediaPipeFaceDetector(
    FACE_MODEL
)

print("FACE DETECTOR READY")


# ============================================================
# TEST GENERATOR
# ============================================================

gen = VideoSequence(
    test,
    det,
    BATCH_SIZE,
    False,
    False
)


# ============================================================
# LOAD DIVERSE MODEL
# ============================================================

print()
print("Loading DIVERSE_400 model...")

model = tf.keras.models.load_model(
    DIVERSE_MODEL_PATH,
    safe_mode=False,
    compile=False
)

print("MODEL LOADED SUCCESSFULLY")


# ============================================================
# MODEL INFORMATION
# ============================================================

print()
print("Model input shape :", model.input_shape)
print("Model output shape:", model.output_shape)


# ============================================================
# PREDICTION
# ============================================================

print()
print("Running predictions...")

scores = model.predict(
    gen,
    verbose=1
).reshape(-1)


# ============================================================
# TRUE LABELS
# ============================================================

y = np.array(
    [
        int(x["label"])
        for x in test
    ],
    dtype=np.int32
)


# ============================================================
# SANITY CHECK
# ============================================================

if len(scores) != len(y):

    raise RuntimeError(
        f"Prediction count mismatch: "
        f"{len(scores)} predictions for "
        f"{len(y)} test videos."
    )


# ============================================================
# FIXED THRESHOLD
# ============================================================
#
# IMPORTANT:
# Keep exactly the same threshold used by evaluate.py.
#
# This makes the comparison between:
#
# OLD_50_50_RECOVERED.keras
#
# and
#
# DIVERSE_322.keras
#
# fair.
#

THRESHOLD = 0.45


predictions = (
    scores >= THRESHOLD
).astype(np.int32)


# ============================================================
# METRICS
# ============================================================

roc_auc = roc_auc_score(
    y,
    scores
)

accuracy = accuracy_score(
    y,
    predictions
)

precision = precision_score(
    y,
    predictions,
    zero_division=0
)

recall = recall_score(
    y,
    predictions,
    zero_division=0
)

f1 = f1_score(
    y,
    predictions,
    zero_division=0
)

cm = confusion_matrix(
    y,
    predictions
)


# ============================================================
# RESULTS
# ============================================================

print()
print("=" * 70)
print("FINAL DIVERSE TEST RESULTS")
print("=" * 70)

print(
    f"Threshold: {THRESHOLD:.2f}"
)

print(
    f"ROC-AUC  : {roc_auc:.4f}"
)

print(
    f"Accuracy : {accuracy:.4f}"
)

print(
    f"Precision: {precision:.4f}"
)

print(
    f"Recall   : {recall:.4f}"
)

print(
    f"F1       : {f1:.4f}"
)


# ============================================================
# CONFUSION MATRIX
# ============================================================

print()
print("Confusion Matrix:")
print(cm)


# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print()
print(
    classification_report(
        y,
        predictions,
        target_names=[
            "REAL",
            "DEEPFAKE"
        ],
        digits=4,
        zero_division=0
    )
)


# ============================================================
# PER-VIDEO RESULTS
# ============================================================

print()
print("=" * 70)
print("VIDEO RESULTS")
print("=" * 70)

print(
    f"{'VIDEO':<22}"
    f"{'TRUE':<12}"
    f"{'SCORE':<12}"
    f"{'PRED':<12}"
    f"{'RESULT'}"
)

print("-" * 70)


for item, true_label, score, pred in zip(
    test,
    y,
    scores,
    predictions
):

    name = Path(
        item["path"]
    ).name

    true_name = (
        "REAL"
        if true_label == 0
        else "DEEPFAKE"
    )

    pred_name = (
        "REAL"
        if pred == 0
        else "DEEPFAKE"
    )

    result = (
        "CORRECT"
        if true_label == pred
        else "WRONG"
    )

    print(
        f"{name:<22}"
        f"{true_name:<12}"
        f"{score:<12.4f}"
        f"{pred_name:<12}"
        f"{result}"
    )


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 70)
print("DIVERSE TEST EVALUATION COMPLETE")
print("=" * 70)

print()
print("Model tested:")
print(DIVERSE_MODEL_PATH)

print()
print("Test set:")
print(TEST_MANIFEST)

print()
print("Threshold:")
print(f"{THRESHOLD:.2f}")

print("=" * 70)