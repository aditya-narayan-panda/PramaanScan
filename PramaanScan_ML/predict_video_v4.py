from pathlib import Path
import sys
import argparse
import cv2
import numpy as np
import tensorflow as tf


# ============================================================
# PATH
# ============================================================

ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ============================================================
# PROJECT IMPORTS
# ============================================================

from config import (
    IMG_SIZE,
    SEQ_LEN,
    FACE_MARGIN,
    FACE_MODEL,
)

from src.face import MediaPipeFaceDetector
from src.model import TemporalPositionEmbedding


# ============================================================
# MODEL PATHS
# ============================================================

OLD_MODEL_PATH = (
    ROOT
    / "outputs"
    / "models"
    / "OLD_50_50_RECOVERED.keras"
)

DIVERSE_MODEL_PATH = (
    ROOT
    / "outputs"
    / "models"
    / "DIVERSE_400.keras"
)


# ============================================================
# DEFAULT MODEL
# ============================================================

DEFAULT_MODEL = "diverse"


# ============================================================
# DECISION THRESHOLDS
# ============================================================

OLD_THRESHOLD = 0.39

# Selected ONLY from validation analysis for DIVERSE_400.
# Validation best F1 and best accuracy were both at 0.45.
DIVERSE_THRESHOLD = 0.45


# ============================================================
# TEMPORAL SETTINGS
# ============================================================

WINDOW_SIZE = SEQ_LEN

NUM_WINDOWS = 12


# ============================================================
# EVIDENCE THRESHOLDS
# ============================================================

STRONG_FAKE = 0.70
VERY_STRONG_FAKE = 0.80

STRONG_REAL = 0.30


# ============================================================
# FACE / QUALITY REQUIREMENTS
# ============================================================

MIN_WINDOW_FACE_RATIO = 0.50
MIN_WINDOW_QUALITY = 0.30

LOW_QUALITY_WEIGHT = 0.20


# ============================================================
# TEMPORAL DISAGREEMENT
# ============================================================

DISAGREEMENT_STD = 0.25

BORDER_MARGIN = 0.05


# ============================================================
# RUNTIME
# ============================================================

_MODEL = None
_DETECTOR = None

_ACTIVE_MODEL_NAME = None
_ACTIVE_MODEL_PATH = None
_ACTIVE_THRESHOLD = None


# ============================================================
# MODEL SELECTION
# ============================================================

def _get_model_config(model_name):

    model_name = model_name.lower().strip()

    if model_name == "old":

        return (
            "OLD_50_50_RECOVERED",
            OLD_MODEL_PATH,
            OLD_THRESHOLD
        )

    if model_name == "diverse":

        return (
            "DIVERSE_400",
            DIVERSE_MODEL_PATH,
            DIVERSE_THRESHOLD
        )

    raise ValueError(
        f"Unknown model: {model_name}\n"
        f"Use either 'old' or 'diverse'."
    )


# ============================================================
# MODEL LOADING
# ============================================================

def _load_runtime(model_name):

    global _MODEL
    global _DETECTOR
    global _ACTIVE_MODEL_NAME
    global _ACTIVE_MODEL_PATH
    global _ACTIVE_THRESHOLD

    (
        selected_name,
        selected_path,
        selected_threshold
    ) = _get_model_config(model_name)


    # --------------------------------------------------------
    # Check model
    # --------------------------------------------------------

    if not selected_path.exists():

        raise FileNotFoundError(
            f"\nModel not found:\n"
            f"{selected_path}\n"
        )


    # --------------------------------------------------------
    # Face detector
    # --------------------------------------------------------

    if _DETECTOR is None:

        print()
        print("Initializing face detector...")

        _DETECTOR = MediaPipeFaceDetector(
            FACE_MODEL
        )

        print("FACE DETECTOR READY")


    # --------------------------------------------------------
    # Model
    # --------------------------------------------------------

    if (
        _MODEL is None
        or
        _ACTIVE_MODEL_PATH != selected_path
    ):

        print()
        print(
            f"Loading {selected_name} model..."
        )

        _MODEL = tf.keras.models.load_model(
            selected_path,
            safe_mode=False,
            compile=False
        )

        _ACTIVE_MODEL_NAME = selected_name
        _ACTIVE_MODEL_PATH = selected_path
        _ACTIVE_THRESHOLD = selected_threshold

        print("MODEL LOADED SUCCESSFULLY")

        print(
            "Input shape :",
            _MODEL.input_shape
        )

        print(
            "Output shape:",
            _MODEL.output_shape
        )

        print(
            f"Decision threshold: "
            f"{_ACTIVE_THRESHOLD:.2f}"
        )


    return (
        _MODEL,
        _DETECTOR,
        _ACTIVE_THRESHOLD
    )


# ============================================================
# VIDEO OPENING
# ============================================================

def _open_video(video_path):

    cap = cv2.VideoCapture(
        str(video_path)
    )

    if not cap.isOpened():

        raise RuntimeError(
            f"Could not open video:\n"
            f"{video_path}"
        )

    fps = float(
        cap.get(cv2.CAP_PROP_FPS)
        or 0.0
    )

    if fps <= 0:

        fps = 30.0


    total = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    if total <= 0:

        cap.release()

        raise RuntimeError(
            "Video contains no readable frames."
        )


    duration = total / fps


    return (
        cap,
        fps,
        total,
        duration
    )


# ============================================================
# TEMPORAL WINDOWS
# ============================================================

def _create_windows(
    total_frames,
    window_size,
    num_windows
):

    if total_frames <= 0:

        return []


    if total_frames <= window_size:

        return [
            np.linspace(
                0,
                total_frames - 1,
                window_size
            ).astype(int)
        ]


    max_start = (
        total_frames -
        window_size
    )


    if num_windows <= 1:

        starts = [0]

    else:

        starts = np.linspace(
            0,
            max_start,
            num_windows
        ).astype(int)


    windows = []


    for start in starts:

        indices = np.linspace(
            start,
            start + window_size - 1,
            window_size
        ).astype(int)

        windows.append(
            indices
        )


    return windows


# ============================================================
# FRAME READING
# ============================================================

def _read_required_frames(
    cap,
    required_indices
):

    required_indices = sorted(
        set(
            int(x)
            for x in required_indices
            if int(x) >= 0
        )
    )


    decoded = {}


    if not required_indices:

        return decoded


    print(
        "Reading required frames once..."
    )


    max_required = max(
        required_indices
    )


    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        0
    )


    frame_number = 0


    while frame_number <= max_required:

        ok, frame = cap.read()

        if not ok:

            break


        if frame_number in required_indices:

            rgb = cv2.cvtColor(
                frame,
                cv2.COLOR_BGR2RGB
            )

            decoded[
                frame_number
            ] = rgb


        frame_number += 1


    # --------------------------------------------------------
    # Recovery
    # --------------------------------------------------------

    missing = [
        x
        for x in required_indices
        if x not in decoded
    ]


    if missing:

        for index in missing:

            print(
                f"WARNING: Required frame "
                f"{index} was unavailable."
            )


            if decoded:

                nearest = min(
                    decoded.keys(),
                    key=lambda x:
                    abs(x - index)
                )

                decoded[index] = decoded[
                    nearest
                ]

                print(
                    f"         Using nearest "
                    f"decoded frame {nearest}."
                )

            else:

                decoded[index] = None


    return decoded


# ============================================================
# FACE EXTRACTION
# ============================================================

def _extract_face(
    rgb,
    detector
):

    if rgb is None:

        return (
            None,
            0.0
        )


    try:

        face, detection_score = (
            detector.crop(
                rgb,
                FACE_MARGIN
            )
        )

    except Exception:

        return (
            None,
            0.0
        )


    if face is None:

        return (
            None,
            0.0
        )


    face = cv2.resize(
        face,
        (
            IMG_SIZE,
            IMG_SIZE
        ),
        interpolation=cv2.INTER_AREA
    )


    face = np.asarray(
        face,
        dtype=np.float32
    )


    return (
        face,
        float(detection_score)
    )


# ============================================================
# QUALITY ESTIMATION
# ============================================================

def _frame_quality(
    face,
    detection_score
):

    if face is None:

        return 0.0


    try:

        gray = cv2.cvtColor(
            face.astype(np.uint8),
            cv2.COLOR_RGB2GRAY
        )


        sharpness = cv2.Laplacian(
            gray,
            cv2.CV_64F
        ).var()


        sharpness_score = np.clip(
            sharpness / 250.0,
            0.0,
            1.0
        )


        detection = np.clip(
            float(detection_score),
            0.0,
            1.0
        )


        quality = (
            0.65 * detection
            +
            0.35 * sharpness_score
        )


        return float(
            np.clip(
                quality,
                0.0,
                1.0
            )
        )


    except Exception:

        return float(
            np.clip(
                detection_score,
                0.0,
                1.0
            )
        )


# ============================================================
# PREPROCESSING
# ============================================================

def _preprocess_face(face):

    tensor = tf.convert_to_tensor(
        face,
        dtype=tf.float32
    )


    tensor = (
        tf.keras.applications.efficientnet_v2
        .preprocess_input(
            tensor
        )
    )


    return tensor.numpy()


# ============================================================
# PREPARE TEMPORAL WINDOW
# ============================================================

def _prepare_window(
    indices,
    frame_cache,
    detector
):

    faces = []

    qualities = []

    last_face = None

    last_quality = 0.0

    face_count = 0


    for index in indices:

        rgb = frame_cache.get(
            int(index)
        )


        face, detection_score = (
            _extract_face(
                rgb,
                detector
            )
        )


        if face is not None:

            last_face = face.copy()

            last_quality = (
                _frame_quality(
                    face,
                    detection_score
                )
            )

            current_face = face

            current_quality = (
                last_quality
            )

            face_count += 1


        elif last_face is not None:

            current_face = (
                last_face.copy()
            )

            last_quality *= 0.55

            current_quality = (
                last_quality
            )


        else:

            current_face = np.zeros(
                (
                    IMG_SIZE,
                    IMG_SIZE,
                    3
                ),
                dtype=np.float32
            )

            current_quality = 0.0


        current_face = (
            _preprocess_face(
                current_face
            )
        )


        faces.append(
            current_face
        )

        qualities.append(
            current_quality
        )


    faces = np.asarray(
        faces,
        dtype=np.float32
    )


    qualities = np.asarray(
        qualities,
        dtype=np.float32
    )


    face_ratio = (
        face_count /
        max(len(indices), 1)
    )


    mean_quality = float(
        np.mean(
            qualities
        )
    )


    return (
        faces,
        face_ratio,
        mean_quality
    )


# ============================================================
# SAFE MODEL PREDICTION
# ============================================================

def _predict_batch(
    model,
    batch
):

    if len(batch) == 0:

        return np.asarray([])


    x = np.asarray(
        batch,
        dtype=np.float32
    )


    try:

        predictions = model.predict(
            {
                "video": x
            },
            verbose=0
        )


    except Exception:

        predictions = model.predict(
            x,
            verbose=0
        )


    predictions = np.asarray(
        predictions
    ).reshape(-1)


    predictions = np.clip(
        predictions,
        0.0,
        1.0
    )


    return predictions


# ============================================================
# WINDOW WEIGHT
# ============================================================

def _calculate_window_weight(
    face_ratio,
    quality
):

    if (
        face_ratio < MIN_WINDOW_FACE_RATIO
        or
        quality < MIN_WINDOW_QUALITY
    ):

        return LOW_QUALITY_WEIGHT


    face_component = np.clip(
        face_ratio,
        0.0,
        1.0
    )


    quality_component = np.clip(
        quality,
        0.0,
        1.0
    )


    weight = (
        0.45 * face_component
        +
        0.55 * quality_component
    )


    return float(
        np.clip(
            weight,
            0.20,
            1.0
        )
    )


# ============================================================
# WEIGHTED MEAN
# ============================================================

def _weighted_mean(
    scores,
    weights
):

    scores = np.asarray(
        scores,
        dtype=np.float32
    )


    weights = np.asarray(
        weights,
        dtype=np.float32
    )


    if len(scores) == 0:

        return 0.5


    total_weight = float(
        np.sum(weights)
    )


    if total_weight <= 0:

        return float(
            np.mean(scores)
        )


    return float(
        np.sum(
            scores * weights
        )
        /
        total_weight
    )


# ============================================================
# ROBUST TEMPORAL AGGREGATION
# ============================================================

def _aggregate_evidence(
    scores,
    weights,
    reliable
):

    scores = np.asarray(
        scores,
        dtype=np.float32
    )


    weights = np.asarray(
        weights,
        dtype=np.float32
    )


    reliable_scores = [
        float(s)
        for s, r in zip(
            scores,
            reliable
        )
        if r
    ]


    reliable_weights = [
        float(w)
        for w, r in zip(
            weights,
            reliable
        )
        if r
    ]


    if not reliable_scores:

        reliable_scores = [
            float(x)
            for x in scores
        ]

        reliable_weights = [
            float(x)
            for x in weights
        ]


    reliable_scores = np.asarray(
        reliable_scores,
        dtype=np.float32
    )


    reliable_weights = np.asarray(
        reliable_weights,
        dtype=np.float32
    )


    weighted_mean = _weighted_mean(
        reliable_scores,
        reliable_weights
    )


    median = float(
        np.median(
            reliable_scores
        )
    )


    if len(reliable_scores) >= 5:

        sorted_scores = np.sort(
            reliable_scores
        )

        trimmed = sorted_scores[
            1:-1
        ]

        trimmed_mean = float(
            np.mean(trimmed)
        )

    else:

        trimmed_mean = weighted_mean


    base_score = (
        0.55 * weighted_mean
        +
        0.25 * median
        +
        0.20 * trimmed_mean
    )


    strong_fake_count = int(
        np.sum(
            reliable_scores >= STRONG_FAKE
        )
    )


    very_strong_fake_count = int(
        np.sum(
            reliable_scores >= VERY_STRONG_FAKE
        )
    )


    strong_real_count = int(
        np.sum(
            reliable_scores <= STRONG_REAL
        )
    )


    if strong_fake_count >= 1:

        base_score += 0.08


    if strong_fake_count >= 2:

        base_score += 0.07


    if very_strong_fake_count >= 1:

        base_score += 0.05


    if (
        strong_real_count >= 5
        and
        strong_fake_count == 0
    ):

        base_score -= 0.04


    evidence_score = float(
        np.clip(
            base_score,
            0.0,
            1.0
        )
    )


    std = float(
        np.std(
            reliable_scores
        )
    )


    return {
        "weighted_mean": weighted_mean,
        "median": median,
        "trimmed_mean": trimmed_mean,
        "evidence_score": evidence_score,
        "std": std,
        "strong_fake_count": strong_fake_count,
        "very_strong_fake_count":
            very_strong_fake_count,
        "strong_real_count":
            strong_real_count,
        "reliable_scores":
            reliable_scores,
    }


# ============================================================
# FINAL DECISION
# ============================================================

def _make_decision(
    evidence,
    reliable_count,
    total_count,
    window_info,
    decision_threshold
):

    score = float(
        evidence["evidence_score"]
    )

    std = float(
        evidence["std"]
    )


    strong_fake = int(
        evidence["strong_fake_count"]
    )

    very_strong_fake = int(
        evidence["very_strong_fake_count"]
    )

    strong_real = int(
        evidence["strong_real_count"]
    )


    if reliable_count < 2:

        return (
            "UNCERTAIN",
            "LOW",
            "Too little reliable facial evidence."
        )


    reliable_windows = [
        x
        for x in window_info
        if x.get("reliable", False)
    ]


    strongest_window = None


    if reliable_windows:

        strongest_window = max(
            reliable_windows,
            key=lambda x:
            float(x["score"])
        )


    strongest_score = (
        float(strongest_window["score"])
        if strongest_window is not None
        else 0.0
    )


    strongest_quality = (
        float(strongest_window["quality"])
        if strongest_window is not None
        else 0.0
    )


    # --------------------------------------------------------
    # HARD REAL GUARD
    # --------------------------------------------------------

    if (
        score < decision_threshold
        and
        strong_fake == 0
        and
        very_strong_fake == 0
    ):

        if strong_real >= 4 and std < 0.25:

            return (
                "REAL",
                "HIGH",
                "Reliable temporal windows consistently "
                "support real-video evidence."
            )


        if strong_real >= 2:

            return (
                "REAL",
                "MEDIUM",
                "Overall temporal evidence is below "
                "the deepfake decision threshold."
            )


        return (
            "UNCERTAIN",
            "LOW",
            "Overall evidence is below the deepfake "
            "threshold, but there is not enough "
            "consistent real-video evidence."
        )


    # --------------------------------------------------------
    # STRONG SUSTAINED FAKE
    # --------------------------------------------------------

    if (
        very_strong_fake >= 2
        or
        strong_fake >= 3
    ):

        return (
            "FAKE",
            "HIGH",
            "Multiple reliable temporal regions "
            "show strong deepfake evidence."
        )


    # --------------------------------------------------------
    # VERY STRONG LOCALIZED FAKE
    # --------------------------------------------------------

    if (
        very_strong_fake >= 1
        and
        strongest_score >= VERY_STRONG_FAKE
        and
        strongest_quality >= MIN_WINDOW_QUALITY
    ):

        if score >= 0.35:

            return (
                "FAKE",
                "HIGH",
                "A very strong high-quality temporal "
                "region shows deepfake evidence."
            )


        return (
            "UNCERTAIN",
            "MEDIUM",
            "A very strong localized fake signal was "
            "detected, but overall temporal evidence "
            "is still weak."
        )


    # --------------------------------------------------------
    # HIGH OVERALL FAKE
    # --------------------------------------------------------

    if score >= 0.62:

        return (
            "FAKE",
            "HIGH" if strong_fake >= 2 else "MEDIUM",
            "Overall temporal evidence supports "
            "a manipulated video."
        )


    # --------------------------------------------------------
    # ONE STRONG FAKE REGION
    # --------------------------------------------------------

    if (
        strong_fake >= 1
        and
        strongest_score >= STRONG_FAKE
    ):

        if score < (
            decision_threshold -
            BORDER_MARGIN
        ):

            return (
                "UNCERTAIN",
                "MEDIUM",
                "A strong fake signal was found in one "
                "temporal region, but the overall evidence "
                "is too weak for a confident FAKE verdict."
            )


        return (
            "UNCERTAIN",
            "MEDIUM",
            "A strong fake signal was found, but the "
            "temporal evidence is not sufficiently "
            "consistent for a confident FAKE verdict."
        )


    # --------------------------------------------------------
    # TEMPORAL DISAGREEMENT
    # --------------------------------------------------------

    if (
        std >= DISAGREEMENT_STD
        and
        score >= (
            decision_threshold -
            BORDER_MARGIN
        )
        and
        score <= (
            decision_threshold +
            BORDER_MARGIN
        )
    ):

        return (
            "UNCERTAIN",
            "MEDIUM",
            "Temporal regions disagree strongly."
        )


    # --------------------------------------------------------
    # BORDER ZONE
    # --------------------------------------------------------

    lower_border = (
        decision_threshold -
        BORDER_MARGIN
    )

    upper_border = (
        decision_threshold +
        BORDER_MARGIN
    )


    if (
        lower_border <= score <= upper_border
    ):

        return (
            "UNCERTAIN",
            "MEDIUM",
            "Evidence is close to the decision boundary."
        )


    # --------------------------------------------------------
    # REAL
    # --------------------------------------------------------

    if (
        score < decision_threshold
        and
        strong_real >= 3
    ):

        if std < 0.20:

            return (
                "REAL",
                "HIGH",
                "Reliable temporal windows consistently "
                "support real-video evidence."
            )


        return (
            "REAL",
            "MEDIUM",
            "Overall temporal evidence supports "
            "a real video."
        )


    # --------------------------------------------------------
    # FALLBACK
    # --------------------------------------------------------

    if score < decision_threshold:

        return (
            "UNCERTAIN",
            "LOW",
            "The temporal evidence is below the "
            "deepfake threshold but remains inconclusive."
        )


    return (
        "UNCERTAIN",
        "LOW",
        "The temporal evidence is inconclusive."
    )


# ============================================================
# MAIN VIDEO ANALYSIS
# ============================================================

def analyze_video(
    video_path,
    model_name=DEFAULT_MODEL
):

    video_path = Path(
        video_path
    )


    if not video_path.exists():

        raise FileNotFoundError(
            f"Input does not exist:\n"
            f"{video_path}"
        )


    print()
    print("=" * 70)
    print("PRAMAANSCAN FINAL VIDEO ANALYSIS")
    print("=" * 70)


    model, detector, threshold = (
        _load_runtime(
            model_name
        )
    )


    print()
    print(
        f"Selected model : "
        f"{_ACTIVE_MODEL_NAME}"
    )

    print(
        f"Model path     : "
        f"{_ACTIVE_MODEL_PATH}"
    )

    print(
        f"Threshold      : "
        f"{threshold:.2f}"
    )


    cap, fps, total, duration = (
        _open_video(
            video_path
        )
    )


    print(
        f"FPS: {fps:.2f}"
    )

    print(
        f"Duration: {duration:.2f}s"
    )

    print(
        f"Frames extracted: {total}"
    )


    windows = _create_windows(
        total,
        WINDOW_SIZE,
        NUM_WINDOWS
    )


    print(
        f"Temporal windows: "
        f"{len(windows)}"
    )

    print(
        f"Frames per window: "
        f"{WINDOW_SIZE}"
    )


    unique_indices = sorted(
        set(
            int(i)
            for window in windows
            for i in window
        )
    )


    print(
        f"Unique frames analyzed: "
        f"{len(unique_indices)}"
    )


    frame_cache = (
        _read_required_frames(
            cap,
            unique_indices
        )
    )


    cap.release()


    print(
        "Detecting faces and "
        "preparing temporal batches..."
    )


    batches = []

    window_info = []


    for window_number, indices in enumerate(
        windows,
        start=1
    ):

        faces, face_ratio, quality = (
            _prepare_window(
                indices,
                frame_cache,
                detector
            )
        )


        batches.append(
            faces
        )


        reliable = (
            face_ratio >=
            MIN_WINDOW_FACE_RATIO
            and
            quality >=
            MIN_WINDOW_QUALITY
        )


        weight = (
            _calculate_window_weight(
                face_ratio,
                quality
            )
        )


        window_info.append(
            {
                "index":
                    window_number,

                "face_ratio":
                    face_ratio,

                "quality":
                    quality,

                "reliable":
                    reliable,

                "weight":
                    weight,

                "score":
                    None,
            }
        )


    print(
        "Running batched temporal "
        "model inference..."
    )


    batch = np.asarray(
        batches,
        dtype=np.float32
    )


    predictions = _predict_batch(
        model,
        batch
    )


    scores = []

    weights = []

    reliable_flags = []


    for info, prediction in zip(
        window_info,
        predictions
    ):

        score = float(
            np.clip(
                prediction,
                0.0,
                1.0
            )
        )


        info["score"] = score


        scores.append(
            score
        )


        weights.append(
            info["weight"]
        )


        reliable_flags.append(
            info["reliable"]
        )


        if info["reliable"]:

            evidence_label = (
                "RELIABLE"
            )

        else:

            evidence_label = (
                "LOW-EVIDENCE"
            )


        print(
            f"Window "
            f"{info['index']:02d}: "
            f"{score * 100:6.2f}% | "
            f"faces "
            f"{int(round(info['face_ratio'] * WINDOW_SIZE)):02d}/"
            f"{WINDOW_SIZE} | "
            f"quality "
            f"{info['quality']:.3f} | "
            f"{evidence_label}"
        )


    # --------------------------------------------------------
    # Aggregate
    # --------------------------------------------------------

    evidence = _aggregate_evidence(
        scores,
        weights,
        reliable_flags
    )


    reliable_count = int(
        sum(
            reliable_flags
        )
    )


    total_count = len(
        scores
    )


    verdict, confidence, explanation = (
        _make_decision(
            evidence,
            reliable_count,
            total_count,
            window_info,
            threshold
        )
    )


    strong_fake_regions = []


    for info in window_info:

        if (
            info["reliable"]
            and
            info["score"] >= STRONG_FAKE
        ):

            strong_fake_regions.append(
                [
                    info["index"],
                    info["index"]
                ]
            )


    average_face_ratio = float(
        np.mean(
            [
                x["face_ratio"]
                for x in window_info
            ]
        )
    )


    average_quality = float(
        np.mean(
            [
                x["quality"]
                for x in window_info
            ]
        )
    )


    faces_detected = int(
        sum(
            round(
                x["face_ratio"] *
                WINDOW_SIZE
            )
            for x in window_info
        )
    )


    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 70)
    print("FINAL TEMPORAL EVIDENCE SUMMARY")
    print("=" * 70)


    print(
        f"Weighted mean          : "
        f"{evidence['weighted_mean'] * 100:.2f}%"
    )


    print(
        f"Median                 : "
        f"{evidence['median'] * 100:.2f}%"
    )


    print(
        f"Evidence score         : "
        f"{evidence['evidence_score'] * 100:.2f}%"
    )


    print(
        f"Temporal variation     : "
        f"{evidence['std'] * 100:.2f}%"
    )


    print(
        f"Reliable windows       : "
        f"{reliable_count}/{total_count}"
    )


    print(
        f"Strong fake windows    : "
        f"{evidence['strong_fake_count']}/"
        f"{total_count}"
    )


    print(
        f"Very strong fake       : "
        f"{evidence['very_strong_fake_count']}/"
        f"{total_count}"
    )


    print(
        f"Strong real windows    : "
        f"{evidence['strong_real_count']}/"
        f"{total_count}"
    )


    print(
        f"Average face ratio     : "
        f"{average_face_ratio * 100:.1f}%"
    )


    print(
        f"Average face quality   : "
        f"{average_quality:.3f}"
    )


    if strong_fake_regions:

        print(
            "Strong fake regions    : "
            f"{strong_fake_regions}"
        )

    else:

        print(
            "Strong fake regions    : NONE"
        )


    # ========================================================
    # FINAL RESULT
    # ========================================================

    print()
    print("=" * 70)
    print("FINAL PRAMAANSCAN RESULT")
    print("=" * 70)


    print(
        f"Video                   : "
        f"{video_path.name}"
    )


    print(
        f"Model                   : "
        f"{_ACTIVE_MODEL_NAME}"
    )


    print(
        f"Base probability        : "
        f"{evidence['evidence_score'] * 100:.2f}%"
    )


    print(
        f"Decision threshold      : "
        f"{threshold * 100:.2f}%"
    )


    print(
        f"Verdict                 : "
        f"{verdict}"
    )


    print(
        f"Confidence              : "
        f"{confidence}"
    )


    print(
        f"Explanation             : "
        f"{explanation}"
    )


    print(
        f"Frames extracted        : "
        f"{total}"
    )


    print(
        f"Frames analyzed         : "
        f"{len(unique_indices)}"
    )


    print(
        f"Faces detected          : "
        f"{faces_detected}/"
        f"{len(unique_indices)}"
    )


    print("=" * 70)


    # ========================================================
    # API RESULT
    # ========================================================

    return {

        "filename":
            video_path.name,

        "media_type":
            "video",

        "model":
            _ACTIVE_MODEL_NAME,

        "verdict":
            verdict,

        "confidence":
            confidence,

        "fake_probability":
            round(
                evidence["evidence_score"],
                6
            ),

        "base_probability":
            round(
                evidence["weighted_mean"],
                6
            ),

        "threshold":
            threshold,

        "explanation":
            explanation,

        "frames_extracted":
            total,

        "frames_analyzed":
            len(unique_indices),

        "faces_detected":
            faces_detected,

        "face_ratio":
            round(
                average_face_ratio,
                4
            ),

        "face_quality":
            round(
                average_quality,
                4
            ),

        "reliable_windows":
            reliable_count,

        "total_windows":
            total_count,

        "strong_fake_windows":
            evidence[
                "strong_fake_count"
            ],

        "very_strong_fake_windows":
            evidence[
                "very_strong_fake_count"
            ],

        "strong_real_windows":
            evidence[
                "strong_real_count"
            ],

        "temporal_std":
            round(
                evidence["std"],
                6
            ),

        "window_scores":
            [
                round(
                    float(x),
                    6
                )
                for x in scores
            ],

        "strong_fake_regions":
            strong_fake_regions,
    }


# ============================================================
# COMPATIBILITY WRAPPER
# ============================================================

def main(
    video_path,
    model_name=DEFAULT_MODEL
):

    return analyze_video(
        video_path,
        model_name
    )


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "PramaanScan final video "
            "deepfake analysis"
        )
    )


    parser.add_argument(
        "video",
        help="Path to input video"
    )


    parser.add_argument(
        "--model",
        choices=[
            "old",
            "diverse"
        ],
        default=DEFAULT_MODEL,
        help=(
            "Model to use: "
            "old or diverse"
        )
    )


    args = parser.parse_args()


    try:

        main(
            args.video,
            args.model
        )


    except KeyboardInterrupt:

        print(
            "\nAnalysis cancelled."
        )

        sys.exit(1)


    except Exception as exc:

        print()
        print("=" * 70)
        print("PRAMAANSCAN ERROR")
        print("=" * 70)

        print(
            str(exc)
        )

        sys.exit(1)