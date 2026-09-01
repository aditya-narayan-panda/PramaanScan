"""
PramaanScan Audio Model — Retraining Script
=============================================

Fixes the overfitting problem from training on only 21 files by:
  1. Slicing every source audio file into 5-second chunks (more training
     examples per file, and matches the ~8s segment window your live
     predictor already uses at inference time).
  2. Reusing the EXACT SAME feature extraction function your live
     predictor.py uses (extract_features_from_array) — this is critical,
     training and inference must use identical features or the retrained
     model won't work correctly with your existing code.
  3. Retraining the same 3 models (SVM, Random Forest, Logistic
     Regression) your app already loads, and overwriting the same .pkl
     paths — no other code changes needed after this runs.
  4. Saving a training_metadata.json with real accuracy numbers, in the
     same format your image_ml module already produces — so you have a
     comparable, citable number for your demo.

DATASET FORMAT EXPECTED
------------------------
Point DATASET_DIR at a folder like this:

    dataset/
        real/       <- genuine human speech clips (.wav, .mp3, .flac...)
        fake/       <- AI-generated / synthetic speech clips

Good free, legitimate sources for this (NOT scraped from YouTube —
scraping raises real copyright/ToS problems, and undeclared data
sourcing is exactly what your hackathon's plagiarism/conduct rules
flag):
  - "Fake-or-Real" (FoR) dataset — built specifically for this task
  - ASVspoof 2019/2021 (LA) — the standard academic benchmark
  - WaveFake

USAGE
-----
    pip install librosa soundfile scikit-learn joblib numpy tqdm
    python retrain_audio.py --dataset ./dataset --chunk-seconds 5
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import librosa
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from tqdm import tqdm

# --------------------------------------------------------------
# Reuse the EXACT feature extraction from the live predictor.
# --------------------------------------------------------------
AUDIO_MODULE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(AUDIO_MODULE_DIR))

from predictor import SAMPLE_RATE, extract_features_from_array  # noqa: E402

MODEL_DIR = AUDIO_MODULE_DIR / "models"
LABELS = {"real": 0, "fake": 1}  # matches classes_ order predictor.py expects


def chunk_audio(audio: np.ndarray, sr: int, chunk_seconds: float) -> list[np.ndarray]:
    """Slice one audio array into non-overlapping chunk_seconds-long pieces.
    Drops a final partial chunk shorter than half the target length."""
    chunk_len = int(chunk_seconds * sr)
    min_len = chunk_len // 2
    chunks = []
    for start in range(0, len(audio), chunk_len):
        piece = audio[start : start + chunk_len]
        if len(piece) >= min_len:
            chunks.append(piece)
    return chunks


def load_dataset(dataset_dir: Path, chunk_seconds: float):
    X, y = [], []
    audio_extensions = {".wav", ".mp3", ".flac", ".m4a", ".ogg"}

    for label_name, label_value in LABELS.items():
        class_dir = dataset_dir / label_name
        if not class_dir.exists():
            raise SystemExit(
                f"Expected folder not found: {class_dir}\n"
                f"Dataset must have real/ and fake/ subfolders."
            )

        files = [f for f in class_dir.iterdir() if f.suffix.lower() in audio_extensions]
        print(f"\n{label_name}: {len(files)} source files")

        for f in tqdm(files, desc=f"Extracting features [{label_name}]"):
            try:
                audio, sr = librosa.load(f, sr=SAMPLE_RATE, mono=True)
            except Exception as exc:
                print(f"  Skipping {f.name}: could not load ({exc})")
                continue

            for chunk in chunk_audio(audio, sr, chunk_seconds):
                try:
                    features = extract_features_from_array(chunk, sr=sr)
                    X.append(features)
                    y.append(label_value)
                except Exception as exc:
                    print(f"  Skipping a chunk of {f.name}: {exc}")

    return np.array(X, dtype=np.float64), np.array(y, dtype=np.int64)


def evaluate(name, model, X_test, y_test):
    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy": float(accuracy_score(y_test, pred)),
        "precision": float(precision_score(y_test, pred)),
        "recall": float(recall_score(y_test, pred)),
        "f1": float(f1_score(y_test, pred)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "confusion_matrix": confusion_matrix(y_test, pred).tolist(),
    }, proba


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, required=True, help="Path to dataset/ with real/ and fake/ subfolders")
    parser.add_argument("--chunk-seconds", type=float, default=5.0)
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    print("=" * 70)
    print("PRAMAANSCAN AUDIO MODEL — RETRAINING")
    print("=" * 70)

    X, y = load_dataset(args.dataset, args.chunk_seconds)
    print(f"\nTotal training examples after chunking: {len(X)} ({X.shape[1]} features each)")
    print(f"  real: {int((y == 0).sum())}   fake: {int((y == 1).sum())}")

    if len(X) < 50:
        print(
            "\nWARNING: still under 50 total examples after chunking. "
            "This will likely still overfit — get more source files if possible."
        )

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=args.test_size, random_state=42, stratify=y
    )

    # NOTE: no StandardScaler here — your live predictor.py feeds raw,
    # unscaled features directly into model.predict_proba(). Training on
    # scaled features while inference uses raw features would silently
    # break predictions, so we train on raw features to match exactly.

    models = {
        "svm": SVC(kernel="rbf", probability=True, random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=200, max_depth=12, min_samples_leaf=3, random_state=42
        ),
        "logistic": LogisticRegression(max_iter=2000, random_state=42),
    }

    metrics = {}
    probas = {}
    print("\nTraining models...")
    for name, model in models.items():
        model.fit(X_train, y_train)
        metrics[name], probas[name] = evaluate(name, model, X_test, y_test)
        print(f"  {name}: accuracy={metrics[name]['accuracy']:.3f}  f1={metrics[name]['f1']:.3f}")

    # Soft-voting ensemble, weighted by each model's own accuracy
    # (same scheme as the image module).
    total_acc = sum(metrics[m]["accuracy"] for m in models)
    weights = {m: metrics[m]["accuracy"] / total_acc for m in models}

    ensemble_proba = sum(weights[m] * probas[m] for m in models)
    ensemble_pred = (ensemble_proba >= 0.5).astype(int)
    metrics["soft_voting_ensemble"] = {
        "accuracy": float(accuracy_score(y_test, ensemble_pred)),
        "precision": float(precision_score(y_test, ensemble_pred)),
        "recall": float(recall_score(y_test, ensemble_pred)),
        "f1": float(f1_score(y_test, ensemble_pred)),
        "roc_auc": float(roc_auc_score(y_test, ensemble_proba)),
        "confusion_matrix": confusion_matrix(y_test, ensemble_pred).tolist(),
    }

    print(f"\nEnsemble accuracy: {metrics['soft_voting_ensemble']['accuracy']:.3f}")

    # --------------------------------------------------------------
    # Save models — OVERWRITES the existing .pkl files your app loads.
    # Back up the old ones first if you want to compare before/after.
    # --------------------------------------------------------------
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(models["svm"], MODEL_DIR / "svm.pkl")
    joblib.dump(models["random_forest"], MODEL_DIR / "random_forest.pkl")
    joblib.dump(models["logistic"], MODEL_DIR / "logistic_regression.pkl")
    print(f"\nSaved retrained models to: {MODEL_DIR}")

    metadata = {
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_train_samples": int(len(X_train)),
        "n_test_samples": int(len(X_test)),
        "chunk_seconds": args.chunk_seconds,
        "feature_dimension": int(X.shape[1]),
        "label_classes": ["real", "fake"],
        "ensemble_weights": weights,
        "metrics": metrics,
    }
    metadata_path = MODEL_DIR / "training_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2))
    print(f"Saved metrics to: {metadata_path}")

    print("\nDone. Restart your backend to load the retrained models.")


if __name__ == "__main__":
    main()
