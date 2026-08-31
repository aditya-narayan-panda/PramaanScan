from pathlib import Path

import joblib
import librosa
import numpy as np

#from pramaanscan.PramaanScan_ML.src import model


# ============================================================
# AUDIO MODEL PATH
# ============================================================

AUDIO_DIR = Path(__file__).resolve().parent
MODEL_DIR = AUDIO_DIR / "models"

SAMPLE_RATE = 16000

# Inference-time robustness only. The trained feature schema remains
# unchanged at 130 features; we simply inspect several temporal regions
# and combine them with the full-file prediction.
SEGMENT_SECONDS = 8.0
SEGMENT_OVERLAP = 0.50
MAX_SEGMENTS = 7
MIN_SEGMENT_SECONDS = 2.0


# ============================================================
# FEATURE EXTRACTION
# ============================================================

def extract_features_from_array(audio, sr=SAMPLE_RATE):
    """Extract the exact 130-feature schema used by the trained models."""
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)

    if audio.size == 0:
        raise ValueError("Empty audio")

    # Normalize audio consistently with the original predictor.
    peak = float(np.max(np.abs(audio)))
    if peak > 0:
        audio = audio / peak

    features = []

    # ========================================================
    # MFCC
    # ========================================================

    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=sr,
        n_mfcc=20,
    )

    features.extend(np.mean(mfcc, axis=1))
    features.extend(np.std(mfcc, axis=1))

    # ========================================================
    # DELTA MFCC
    # ========================================================

    delta = librosa.feature.delta(mfcc)

    features.extend(np.mean(delta, axis=1))
    features.extend(np.std(delta, axis=1))

    # ========================================================
    # RMS
    # ========================================================

    rms = librosa.feature.rms(y=audio)[0]

    features.extend([
        np.mean(rms),
        np.std(rms),
        np.min(rms),
        np.max(rms),
    ])

    # ========================================================
    # ZERO CROSSING RATE
    # ========================================================

    zcr = librosa.feature.zero_crossing_rate(audio)[0]

    features.extend([
        np.mean(zcr),
        np.std(zcr),
    ])

    # ========================================================
    # SPECTRAL CENTROID
    # ========================================================

    centroid = librosa.feature.spectral_centroid(
        y=audio,
        sr=sr,
    )[0]

    features.extend([
        np.mean(centroid),
        np.std(centroid),
    ])

    # ========================================================
    # SPECTRAL BANDWIDTH
    # ========================================================

    bandwidth = librosa.feature.spectral_bandwidth(
        y=audio,
        sr=sr,
    )[0]

    features.extend([
        np.mean(bandwidth),
        np.std(bandwidth),
    ])

    # ========================================================
    # SPECTRAL ROLLOFF
    # ========================================================

    rolloff = librosa.feature.spectral_rolloff(
        y=audio,
        sr=sr,
    )[0]

    features.extend([
        np.mean(rolloff),
        np.std(rolloff),
    ])

    # ========================================================
    # SPECTRAL CONTRAST
    # ========================================================

    try:
        contrast = librosa.feature.spectral_contrast(
            y=audio,
            sr=sr,
        )

        features.extend(np.mean(contrast, axis=1))
        features.extend(np.std(contrast, axis=1))

    except Exception:
        # Keep the exact original fallback: 7 means + 7 stds.
        features.extend(np.zeros(14))

    # ========================================================
    # CHROMA
    # ========================================================

    chroma = librosa.feature.chroma_stft(
        y=audio,
        sr=sr,
    )

    features.extend(np.mean(chroma, axis=1))
    features.extend(np.std(chroma, axis=1))

    vector = np.asarray(features, dtype=np.float32)

    if vector.shape[0] != 130:
        raise ValueError(
            f"Audio feature schema changed unexpectedly: "
            f"generated {vector.shape[0]} features; expected 130."
        )

    return vector


def extract_features(path):
    """Load a complete audio file and extract the trained feature schema."""
    audio, sr = librosa.load(
        path,
        sr=SAMPLE_RATE,
        mono=True,
    )

    if len(audio) == 0:
        raise ValueError("Empty audio")

    return extract_features_from_array(audio, sr)


# ============================================================
# TEMPORAL AUDIO SAMPLING
# ============================================================

def _make_audio_segments(audio, sr):
    """Return a small set of overlapping regions for temporal robustness."""
    audio = np.asarray(audio, dtype=np.float32).reshape(-1)

    if audio.size == 0:
        return []

    target = max(
        int(round(SEGMENT_SECONDS * sr)),
        1,
    )

    minimum = max(
        int(round(MIN_SEGMENT_SECONDS * sr)),
        1,
    )

    # Short recordings are better represented by the complete waveform.
    if len(audio) <= target:
        return [audio]

    step = max(
        int(round(target * (1.0 - SEGMENT_OVERLAP))),
        1,
    )

    starts = list(range(0, max(len(audio) - target, 0) + 1, step))

    last_start = max(len(audio) - target, 0)
    if not starts or starts[-1] != last_start:
        starts.append(last_start)

    # Keep temporal coverage while bounding inference cost.
    if len(starts) > MAX_SEGMENTS:
        positions = np.linspace(
            0,
            len(starts) - 1,
            MAX_SEGMENTS,
        ).round().astype(int)

        starts = [starts[int(i)] for i in positions]

    segments = []

    for start in starts:
        segment = audio[start:start + target]

        if len(segment) < minimum:
            # This can only happen at an unusually short tail. Avoid
            # discarding it; zero padding keeps the signal deterministic.
            padded = np.zeros(minimum, dtype=np.float32)
            padded[:len(segment)] = segment
            segment = padded

        segments.append(segment)

    return segments


# ============================================================
# LOAD AUDIO MODELS
# ============================================================

RANDOM_FOREST_PATH = MODEL_DIR / "random_forest.pkl"
SVM_PATH = MODEL_DIR / "svm.pkl"
LOGISTIC_REGRESSION_PATH = MODEL_DIR / "logistic_regression.pkl"

for model_path in [
    RANDOM_FOREST_PATH,
    SVM_PATH,
    LOGISTIC_REGRESSION_PATH,
]:
    if not model_path.exists():
        raise FileNotFoundError(
            f"Audio model not found:\n{model_path}"
        )


random_forest = joblib.load(RANDOM_FOREST_PATH)
svm = joblib.load(SVM_PATH)
logistic_regression = joblib.load(LOGISTIC_REGRESSION_PATH)

models = {
    "Random Forest": random_forest,
    "SVM": svm,
    "Logistic Regression": logistic_regression,
}


# ============================================================
# MODEL PREDICTION HELPERS
# ============================================================

def _class_probability(model, probabilities, class_value):
    print("Model classes:", model.classes_)   # added temporarily for debugging


    classes = list(getattr(model, "classes_", []))

    if class_value in classes:
        return float(probabilities[classes.index(class_value)])

    # Defensive support for string labels in future compatible models.
    aliases = {
        1: {"1", "ai", "fake", "synthetic"},
        0: {"0", "human", "real", "genuine"},
    }

    target_aliases = aliases[class_value]

    for index, label in enumerate(classes):
        if str(label).strip().lower() in target_aliases:
            return float(probabilities[index])

    raise ValueError(
        f"Audio model does not expose a recognised class mapping: {classes}"
    )


def _predict_features(features):
    features = np.asarray(features, dtype=np.float32).reshape(1, -1)

    results = {}
    for name, model in models.items():
        expected = getattr(model, "n_features_in_", None)

        if expected is not None and features.shape[1] != expected:
            raise ValueError(
                f"Audio feature mismatch for {name}: "
                f"model expects {expected}, "
                f"but predictor generated {features.shape[1]}."
            )

        probabilities = model.predict_proba(features)[0]

        print("\n======================")
        print(name)
        print("Classes:", model.classes_)
        print("Probabilities:", probabilities) #added temporarily for debugging


        human_score = _class_probability(model, probabilities, 0)
        ai_score = _class_probability(model, probabilities, 1)

        results[name] = {
            "prediction": "AI" if ai_score >= 0.5 else "Human",
            "ai_score": ai_score,
            "human_score": human_score,
        }

    return results


def _robust_segment_score(scores):
    if not scores:
        return 0.5

    values = np.asarray(scores, dtype=np.float32)

    median = float(np.median(values))
    upper_evidence = float(np.percentile(values, 75))

    # Median protects against one bad segment; the upper quartile preserves
    # useful evidence when manipulation is localized to part of a recording.
    return float(
        np.clip(
            0.75 * median + 0.25 * upper_evidence,
            0.0,
            1.0,
        )
    )


# ============================================================
# AUDIO PREDICTION
# ============================================================

def predict_audio(audio_path):
    """
    Predict AI-generated/manipulated audio with the existing trained
    three-model ensemble plus lightweight temporal sampling.

    The original 130-feature schema and saved models are unchanged.
    """

    audio, sr = librosa.load(
        audio_path,
        sr=SAMPLE_RATE,
        mono=True,
    )

    if len(audio) == 0:
        raise ValueError("Empty audio")

    # --------------------------------------------------------
    # Full-file prediction — retained as the strongest baseline
    # --------------------------------------------------------

    whole_features = extract_features_from_array(audio, sr)
    whole_results = _predict_features(whole_features)

    # --------------------------------------------------------
    # Temporal segment predictions
    # --------------------------------------------------------

    segments = _make_audio_segments(audio, sr)

    segment_results = {
        name: []
        for name in models
    }

    for segment in segments:
        segment_features = extract_features_from_array(segment, sr)
        result = _predict_features(segment_features)

        for name, model_result in result.items():
            segment_results[name].append(
                float(model_result["ai_score"])
            )

    # --------------------------------------------------------
    # Robust per-model ensemble
    # --------------------------------------------------------

    results = {}
    ai_scores = []
    human_scores = []

    for name in models:
        whole_ai = float(whole_results[name]["ai_score"])
        segment_ai = _robust_segment_score(segment_results[name])

        # Full-file signal remains dominant to preserve compatibility with
        # the trained distribution; temporal evidence improves robustness.
        final_ai = float(
            np.clip(
                0.65 * whole_ai + 0.35 * segment_ai,
                0.0,
                1.0,
            )
        )

        final_human = float(1.0 - final_ai)

        prediction = "AI" if final_ai >= 0.5 else "Human"

        results[name] = {
            "prediction": prediction,
            "ai_score": final_ai,
            "human_score": final_human,
            "whole_file_ai_score": whole_ai,
            "temporal_ai_score": segment_ai,
            "segments_analyzed": len(segment_results[name]),
        }

        ai_scores.append(final_ai)
        human_scores.append(final_human)

    # Median remains the final ensemble statistic so one model cannot
    # dominate the result.
    average_ai_score = float(np.median(ai_scores))
    average_human_score = float(np.median(human_scores))

    ai_votes = sum(
        1 for score in ai_scores
        if score >= 0.5
    )

    strongest_ai_score = float(max(ai_scores)) if ai_scores else 0.0
    model_spread = (
        float(max(ai_scores) - min(ai_scores))
        if ai_scores
        else 0.0
    )

    # Recall-oriented safety rule:
    # - keep the original majority vote when models agree;
    # - if one trained model crosses the AI boundary while the others
    #   strongly disagree, flag the file instead of silently calling it
    #   human. The score/confidence still exposes that disagreement.
    if ai_votes >= 2:
        final_prediction = "AI"
    elif (
        strongest_ai_score >= 0.50
        and model_spread >= 0.20
    ):
        final_prediction = "AI"
    else:
        final_prediction = "Human"


    # Score used only for UI display.
    # Keep the statistical median for analysis, but expose a score that
    # matches the final prediction shown to the user.

    if final_prediction == "AI":                             ##
        display_ai_score = strongest_ai_score                ##
    else:
        display_ai_score = average_ai_score

    display_human_score = 1.0 - display_ai_score             ### these are added

    #Added print statements for debugging
    print("\n===== FINAL RESULTS =====")
    import json
    print(json.dumps(results, indent=2))
    print("Average AI:", average_ai_score)
    print("Average Human:", average_human_score)
    print("Final:", final_prediction) 
    #Added print statements for debugging

    return {
        "models": results,
        "average_ai_score": display_ai_score,     # changed from average_ai_score to display_ai_score
        "average_human_score": display_human_score, # changed from average_ai_score to display_ai_score
        "ai_votes": ai_votes,
        "total_models": len(models),
        "segments_analyzed": len(segments),
        "strongest_model_ai_score": strongest_ai_score,
        "model_score_spread": model_spread,
        "final_prediction": final_prediction,
    }


# ============================================================
# STANDALONE TEST
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("PRAMAANSCAN AUDIO MODEL")
    print("=" * 70)

    print()
    print("Audio directory:")
    print(AUDIO_DIR)

    print()
    print("Model directory:")
    print(MODEL_DIR)

    print()
    print("Models loaded:")

    for name, model in models.items():
        features = getattr(model, "n_features_in_", "unknown")
        print(
            f"  {name:<22} "
            f"features={features}"
        )

    print()
    print("Audio predictor ready.")
