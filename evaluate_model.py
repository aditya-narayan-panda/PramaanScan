from pathlib import Path
import os
import sys
import cv2
import numpy as np
import tensorflow as tf

from config import IMG_SIZE, SEQ_LEN, FACE_MARGIN, FACE_MODEL, MODEL_PATH
from src.face import MediaPipeFaceDetector
from src.model import TemporalPositionEmbedding  # registers custom layer


# ============================================================
# PramaanScan Model Evaluation
# ============================================================

DEFAULT_DATASET = (
    Path(os.environ.get("USERPROFILE", Path.home()))
    / "Downloads"
    / "PramaanScan_WildDeepfake_Lite"
    / "data"
    / "test"
)

# None = evaluate ALL available samples
MAX_SAMPLES_PER_CLASS = None

# Validation-selected decision threshold
THRESHOLD = 0.47


def print_header(text):
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def load_model_and_detector():
    print_header("LOADING PRAMAANSCAN MODEL")

    print("Loading model...")

    model = tf.keras.models.load_model(
        MODEL_PATH,
        safe_mode=False,
        compile=False,
    )

    print("MODEL LOADED SUCCESSFULLY")
    print("Input shape :", model.input_shape)
    print("Output shape:", model.output_shape)

    print("\nInitializing face detector...")

    detector = MediaPipeFaceDetector(FACE_MODEL)

    print("FACE DETECTOR READY")

    return model, detector


def image_files(folder):
    allowed = {".png", ".jpg", ".jpeg", ".webp"}

    files = [
        p
        for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in allowed
    ]

    def sort_key(p):
        try:
            return (0, int(p.stem))
        except ValueError:
            return (1, p.name.lower())

    return sorted(files, key=sort_key)


def read_sequence(folder, detector):

    files = image_files(folder)

    if not files:
        raise RuntimeError("No image frames found.")

    # Select exactly SEQ_LEN frames across complete sequence
    indices = np.linspace(
        0,
        len(files) - 1,
        SEQ_LEN
    ).astype(int)

    faces = []
    detected = 0
    last_face = None

    for idx in indices:

        image_path = files[int(idx)]

        frame = cv2.imread(str(image_path))

        if frame is None:

            face = None

        else:

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            face, score = detector.crop(
                rgb,
                FACE_MARGIN
            )

        if face is not None:

            face = tf.image.resize(
                face,
                (IMG_SIZE, IMG_SIZE)
            ).numpy()

            last_face = face
            detected += 1

        elif last_face is not None:

            # Same fallback behavior as video pipeline
            face = last_face.copy()

        else:

            face = np.zeros(
                (IMG_SIZE, IMG_SIZE, 3),
                dtype=np.float32
            )

        face = tf.keras.applications.efficientnet_v2.preprocess_input(
            face.astype(np.float32)
        )

        faces.append(face)

    batch = np.asarray(
        [faces],
        dtype=np.float32
    )

    return batch, detected


def predict_folder(model, detector, folder):

    batch, detected = read_sequence(
        folder,
        detector
    )

    score = float(
        model.predict(
            batch,
            verbose=0
        ).reshape(-1)[0]
    )

    return score, detected


def safe_mean(values):
    return float(np.mean(values)) if values else 0.0


def safe_div(a, b):
    return float(a / b) if b else 0.0


def evaluate_class(
    model,
    detector,
    root,
    class_name,
    label,
    limit,
):

    class_root = root / class_name

    if not class_root.exists():

        raise RuntimeError(
            f"Dataset folder does not exist:\n{class_root}"
        )

    folders = sorted([
        p
        for p in class_root.iterdir()
        if p.is_dir()
    ])

    if limit is not None:
        folders = folders[:limit]

    print_header(
        f"EVALUATING {class_name.upper()} SAMPLES"
    )

    print("Root:", class_root)
    print("Samples:", len(folders))

    results = []

    for number, folder in enumerate(
        folders,
        start=1
    ):

        try:

            score, detected = predict_folder(
                model,
                detector,
                folder
            )

            predicted = (
                1
                if score >= THRESHOLD
                else 0
            )

            correct = (
                predicted == label
            )

            results.append({
                "folder": folder.name,
                "score": score,
                "detected": detected,
                "predicted": predicted,
                "correct": correct,
                "actual": label,
            })

            verdict = (
                "FAKE"
                if predicted == 1
                else "REAL"
            )

            mark = (
                "OK"
                if correct
                else "WRONG"
            )

            print(
                f"{number:03d} | "
                f"{folder.name:<14} | "
                f"{score * 100:6.2f}% | "
                f"faces {detected:02d}/{SEQ_LEN} | "
                f"{verdict:<4} | {mark}"
            )

        except Exception as exc:

            print(
                f"{number:03d} | "
                f"{folder.name:<14} | "
                f"ERROR | {exc}"
            )

    return results


def calculate_metrics(
    fake_results,
    real_results,
    threshold
):

    all_results = (
        fake_results +
        real_results
    )

    tp = sum(
        1
        for r in fake_results
        if r["score"] >= threshold
    )

    fn = sum(
        1
        for r in fake_results
        if r["score"] < threshold
    )

    fp = sum(
        1
        for r in real_results
        if r["score"] >= threshold
    )

    tn = sum(
        1
        for r in real_results
        if r["score"] < threshold
    )

    total = (
        tp +
        tn +
        fp +
        fn
    )

    accuracy = safe_div(
        tp + tn,
        total
    )

    precision = safe_div(
        tp,
        tp + fp
    )

    recall = safe_div(
        tp,
        tp + fn
    )

    f1 = safe_div(
        2 * precision * recall,
        precision + recall
    )

    return {
        "threshold": threshold,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "total": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "all_results": all_results,
    }


def print_metric_block(title, metrics):

    print_header(title)

    print(
        f"Threshold : "
        f"{metrics['threshold'] * 100:.2f}%"
    )

    print("\nConfusion Matrix")

    print(
        "                  Pred REAL   Pred FAKE"
    )

    print(
        f"Actual REAL       "
        f"{metrics['tn']:10d}   "
        f"{metrics['fp']:10d}"
    )

    print(
        f"Actual FAKE       "
        f"{metrics['fn']:10d}   "
        f"{metrics['tp']:10d}"
    )

    print("\nMetrics")

    print(
        f"Accuracy   : "
        f"{metrics['accuracy'] * 100:.2f}%"
    )

    print(
        f"Precision  : "
        f"{metrics['precision'] * 100:.2f}%"
    )

    print(
        f"Recall     : "
        f"{metrics['recall'] * 100:.2f}%"
    )

    print(
        f"F1 Score   : "
        f"{metrics['f1'] * 100:.2f}%"
    )


def evaluate_thresholds(
    fake_results,
    real_results
):

    print_header(
        "TEST SET THRESHOLD COMPARISON"
    )

    thresholds = [
        0.39,
        0.40,
        0.43,
        0.47,
        0.49,
        0.50,
        0.55,
        0.58,
        0.60,
        0.63,
    ]

    print(
        "THRESHOLD   ACCURACY   PRECISION   RECALL   F1"
    )

    best = None

    for threshold in thresholds:

        metrics = calculate_metrics(
            fake_results,
            real_results,
            threshold
        )

        print(
            f"{threshold:8.2f}   "
            f"{metrics['accuracy'] * 100:8.2f}%   "
            f"{metrics['precision'] * 100:9.2f}%   "
            f"{metrics['recall'] * 100:6.2f}%   "
            f"{metrics['f1'] * 100:6.2f}%"
        )

        if (
            best is None
            or metrics["f1"] > best["f1"]
        ):
            best = metrics

    print("\nBest test-set F1 threshold:")
    print(
        f"{best['threshold']:.2f}"
    )

    print(
        f"Accuracy : "
        f"{best['accuracy'] * 100:.2f}%"
    )

    print(
        f"Precision: "
        f"{best['precision'] * 100:.2f}%"
    )

    print(
        f"Recall   : "
        f"{best['recall'] * 100:.2f}%"
    )

    print(
        f"F1       : "
        f"{best['f1'] * 100:.2f}%"
    )

    return best


def main():

    limit = MAX_SAMPLES_PER_CLASS

    # Optional command-line override
    if len(sys.argv) >= 2:

        try:

            limit = int(sys.argv[1])

            if limit <= 0:
                raise ValueError

        except ValueError:

            print(
                "Usage: "
                "python evaluate_model.py "
                "[samples_per_class]"
            )

            sys.exit(1)

    dataset_root = DEFAULT_DATASET

    print_header(
        "PRAMAANSCAN MODEL EVALUATION"
    )

    print("Dataset:")
    print(dataset_root)

    if limit is None:
        print(
            "\nSamples per class: ALL"
        )
    else:
        print(
            "\nSamples per class:",
            limit
        )

    print(
        "Sequence length  :",
        SEQ_LEN
    )

    print(
        "Image size       :",
        IMG_SIZE
    )

    print(
        "Threshold        :",
        f"{THRESHOLD * 100:.2f}%"
    )

    if not dataset_root.exists():

        print(
            "\nERROR: Dataset folder "
            "was not found:"
        )

        print(dataset_root)

        sys.exit(1)

    model, detector = (
        load_model_and_detector()
    )

    fake_results = evaluate_class(
        model=model,
        detector=detector,
        root=dataset_root,
        class_name="fake",
        label=1,
        limit=limit,
    )

    real_results = evaluate_class(
        model=model,
        detector=detector,
        root=dataset_root,
        class_name="real",
        label=0,
        limit=limit,
    )

    if not fake_results and not real_results:

        print(
            "\nNo samples were successfully evaluated."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Main evaluation at validation-selected 47% threshold
    # --------------------------------------------------------

    metrics_main = calculate_metrics(
        fake_results,
        real_results,
        THRESHOLD
    )

    print_metric_block(
        "FINAL MODEL EVALUATION - 47% THRESHOLD",
        metrics_main
    )

    # --------------------------------------------------------
    # Class-wise performance
    # --------------------------------------------------------

    fake_correct = sum(
        r["correct"]
        for r in fake_results
    )

    real_correct = sum(
        r["correct"]
        for r in real_results
    )

    print("\nClass-wise performance")

    print(
        f"Fake correctly detected: "
        f"{fake_correct}/{len(fake_results)}"
    )

    print(
        f"Real correctly detected: "
        f"{real_correct}/{len(real_results)}"
    )

    # --------------------------------------------------------
    # Probability distribution
    # --------------------------------------------------------

    fake_scores = [
        r["score"]
        for r in fake_results
    ]

    real_scores = [
        r["score"]
        for r in real_results
    ]

    print("\nProbability distribution")

    print(
        f"Average fake probability "
        f"(actual FAKE): "
        f"{safe_mean(fake_scores) * 100:.2f}%"
    )

    print(
        f"Average fake probability "
        f"(actual REAL): "
        f"{safe_mean(real_scores) * 100:.2f}%"
    )

    if fake_scores:

        print(
            f"Fake probability range   : "
            f"{min(fake_scores) * 100:.2f}% - "
            f"{max(fake_scores) * 100:.2f}%"
        )

    if real_scores:

        print(
            f"Real probability range   : "
            f"{min(real_scores) * 100:.2f}% - "
            f"{max(real_scores) * 100:.2f}%"
        )

    # --------------------------------------------------------
    # Threshold comparison
    # --------------------------------------------------------

    best = evaluate_thresholds(
        fake_results,
        real_results
    )

    # --------------------------------------------------------
    # Interpretation
    # --------------------------------------------------------

    print_header(
        "INTERPRETATION"
    )

    if metrics_main["f1"] >= 0.90:

        print(
            "MODEL STATUS: STRONG"
        )

    elif metrics_main["f1"] >= 0.75:

        print(
            "MODEL STATUS: USABLE BUT NEEDS IMPROVEMENT"
        )

    else:

        print(
            "MODEL STATUS: NEEDS ML IMPROVEMENT"
        )

    print(
        "\nEvaluation complete."
    )


if __name__ == "__main__":
    main()
