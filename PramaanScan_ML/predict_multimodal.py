from pathlib import Path
import sys
import argparse
import subprocess
import tempfile
import json


# ============================================================
# PATH
# ============================================================

ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# ============================================================
# PROJECT IMPORTS
# ============================================================

from predict_video_v4 import analyze_video
from audio.predictor import predict_audio


# ============================================================
# CONFIGURATION
# ============================================================

VIDEO_MODEL = "diverse"

# Audio/video fusion weights.
#
# Video is currently the stronger and tested component,
# so give it more weight than audio.
VIDEO_WEIGHT = 0.75
AUDIO_WEIGHT = 0.25

# Final multimodal decision threshold.
MULTIMODAL_THRESHOLD = 0.50

# If the two modalities strongly disagree, do not blindly
# force a confident result.
DISAGREEMENT_MARGIN = 0.45


# ============================================================
# FFMPEG CHECK
# ============================================================

def get_ffmpeg_executable():
    """Return a usable FFmpeg executable.

    Prefer a system FFmpeg installation, but fall back to the bundled
    imageio-ffmpeg binary so local Windows setups do not fail simply because
    `ffmpeg.exe` is not on PATH.
    """
    import shutil

    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    try:
        import imageio_ffmpeg
        bundled = imageio_ffmpeg.get_ffmpeg_exe()
        if bundled:
            return bundled
    except Exception:
        pass

    return None


def check_ffmpeg():
    executable = get_ffmpeg_executable()
    if not executable:
        return False

    try:
        result = subprocess.run(
            [executable, "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        return result.returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


# ============================================================
# EXTRACT AUDIO
# ============================================================

def extract_audio(video_path, output_path):

    ffmpeg_executable = get_ffmpeg_executable()
    if not ffmpeg_executable:
        raise RuntimeError(
            "FFmpeg is required for video/audio extraction. Install FFmpeg "
            "or ensure imageio-ffmpeg is installed."
        )

    command = [

        ffmpeg_executable,

        "-y",

        "-i",
        str(video_path),

        "-vn",

        "-ac",
        "1",

        "-ar",
        "16000",

        "-c:a",
        "pcm_s16le",

        str(output_path)
    ]

    result = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:

        raise RuntimeError(
            "FFmpeg audio extraction failed.\n\n"
            + result.stderr
        )

    if not output_path.exists():

        raise RuntimeError(
            "FFmpeg completed but audio file "
            "was not created."
        )

    return output_path


# ============================================================
# AUDIO ANALYSIS
# ============================================================

def analyze_audio(video_path):

    print()
    print("=" * 70)
    print("AUDIO ANALYSIS")
    print("=" * 70)

    with tempfile.TemporaryDirectory(
        prefix="pramaanscan_audio_"
    ) as temp_dir:

        temp_dir = Path(temp_dir)

        audio_path = (
            temp_dir
            / "extracted_audio.wav"
        )

        print()
        print("Extracting audio with FFmpeg...")

        extract_audio(
            video_path,
            audio_path
        )

        print("Audio extracted successfully.")

        print()
        print("Running audio models...")

        result = predict_audio(
            str(audio_path)
        )

        print()
        print("Audio model results:")

        for name, model_result in result["models"].items():

            print(
                f"  {name:<22} "
                f"{model_result['prediction']:<8} "
                f"AI={model_result['ai_score'] * 100:.2f}%"
            )

        print()
        print(
            f"Audio median AI score : "
            f"{result['average_ai_score'] * 100:.2f}%"
        )

        print(
            f"AI votes              : "
            f"{result['ai_votes']}/"
            f"{result['total_models']}"
        )

        print(
            f"Audio verdict         : "
            f"{result['final_prediction']}"
        )

        return result


# ============================================================
# VIDEO ANALYSIS
# ============================================================

def analyze_video_component(video_path):

    print()
    print("=" * 70)
    print("VIDEO ANALYSIS")
    print("=" * 70)

    result = analyze_video(
        str(video_path),
        VIDEO_MODEL
    )

    return result


# ============================================================
# MULTIMODAL FUSION
# ============================================================

def fuse_results(
    video_result,
    audio_result
):

    # --------------------------------------------------------
    # VIDEO SCORE
    # --------------------------------------------------------

    video_score = float(
        video_result.get(
            "fake_probability",
            video_result.get(
                "base_probability",
                0.5
            )
        )
    )

    # --------------------------------------------------------
    # AUDIO SCORE
    # --------------------------------------------------------

    audio_score = float(
        audio_result[
            "average_ai_score"
        ]
    )

    # --------------------------------------------------------
    # WEIGHTED FUSION
    # --------------------------------------------------------

    final_score = (

        VIDEO_WEIGHT * video_score

        +

        AUDIO_WEIGHT * audio_score
    )

    # --------------------------------------------------------
    # MODALITY VERDICTS
    # --------------------------------------------------------

    video_verdict = str(
        video_result.get(
            "verdict",
            "UNCERTAIN"
        )
    )

    audio_verdict = str(
        audio_result.get(
            "final_prediction",
            "Human"
        )
    )

    audio_is_fake = (
        audio_verdict == "AI"
    )

    # --------------------------------------------------------
    # AGREEMENT
    # --------------------------------------------------------

    if (
        video_verdict == "FAKE"
        and audio_is_fake
    ):

        agreement = "STRONG_AGREEMENT"

    elif (
        video_verdict == "REAL"
        and not audio_is_fake
    ):

        agreement = "STRONG_AGREEMENT"

    else:

        agreement = "MODALITY_DISAGREEMENT"

    # --------------------------------------------------------
    # FINAL DECISION
    # --------------------------------------------------------

    if final_score >= MULTIMODAL_THRESHOLD:

        final_verdict = "FAKE"

    else:

        final_verdict = "REAL"

    # --------------------------------------------------------
    # DISAGREEMENT PROTECTION
    # --------------------------------------------------------

    score_difference = abs(
        video_score - audio_score
    )

    if (
        agreement == "MODALITY_DISAGREEMENT"
        and
        score_difference >= DISAGREEMENT_MARGIN
    ):

        final_verdict = "UNCERTAIN"

    # --------------------------------------------------------
    # CONFIDENCE
    # --------------------------------------------------------

    distance = abs(
        final_score -
        MULTIMODAL_THRESHOLD
    )

    if final_verdict == "UNCERTAIN":

        confidence = "MEDIUM"

    elif distance >= 0.25:

        confidence = "HIGH"

    elif distance >= 0.10:

        confidence = "MEDIUM"

    else:

        confidence = "LOW"

    # --------------------------------------------------------
    # EXPLANATION
    # --------------------------------------------------------

    if agreement == "STRONG_AGREEMENT":

        if final_verdict == "FAKE":

            explanation = (
                "Both video and audio analysis "
                "support AI/deepfake evidence."
            )

        else:

            explanation = (
                "Both video and audio analysis "
                "support genuine-media evidence."
            )

    elif final_verdict == "UNCERTAIN":

        explanation = (
            "Video and audio modalities disagree "
            "strongly, so the result is marked "
            "UNCERTAIN instead of forcing a verdict."
        )

    elif final_verdict == "FAKE":

        explanation = (
            "Combined multimodal evidence crosses "
            "the deepfake decision threshold."
        )

    else:

        explanation = (
            "Combined multimodal evidence remains "
            "below the deepfake decision threshold."
        )

    return {

        "final_verdict":
            final_verdict,

        "confidence":
            confidence,

        "multimodal_score":
            round(
                final_score,
                6
            ),

        "video_score":
            round(
                video_score,
                6
            ),

        "audio_score":
            round(
                audio_score,
                6
            ),

        "video_verdict":
            video_verdict,

        "audio_verdict":
            audio_verdict,

        "agreement":
            agreement,

        "explanation":
            explanation
    }


# ============================================================
# PRINT FINAL RESULT
# ============================================================

def print_final_result(
    video_path,
    video_result,
    audio_result,
    fusion_result
):

    print()
    print("=" * 70)
    print("PRAMAANSCAN MULTIMODAL FINAL RESULT")
    print("=" * 70)

    print()
    print(
        f"Video              : "
        f"{Path(video_path).name}"
    )

    print()
    print(
        f"Video model        : "
        f"{video_result.get('model', 'DIVERSE_400')}"
    )

    print(
        f"Video probability  : "
        f"{fusion_result['video_score'] * 100:.2f}%"
    )

    print(
        f"Video verdict      : "
        f"{fusion_result['video_verdict']}"
    )

    print()
    print(
        f"Audio AI score     : "
        f"{fusion_result['audio_score'] * 100:.2f}%"
    )

    print(
        f"Audio verdict      : "
        f"{fusion_result['audio_verdict']}"
    )

    print()
    print(
        f"Video weight       : "
        f"{VIDEO_WEIGHT:.2f}"
    )

    print(
        f"Audio weight       : "
        f"{AUDIO_WEIGHT:.2f}"
    )

    print()
    print(
        f"Multimodal score   : "
        f"{fusion_result['multimodal_score'] * 100:.2f}%"
    )

    print(
        f"Agreement          : "
        f"{fusion_result['agreement']}"
    )

    print()
    print("=" * 70)
    print("FINAL PRAMAANSCAN VERDICT")
    print("=" * 70)

    print()
    print(
        f"Verdict            : "
        f"{fusion_result['final_verdict']}"
    )

    print(
        f"Confidence         : "
        f"{fusion_result['confidence']}"
    )

    print(
        f"Explanation        : "
        f"{fusion_result['explanation']}"
    )

    print()
    print("=" * 70)


# ============================================================
# MAIN
# ============================================================

def main(video_path):

    video_path = Path(
        video_path
    )

    if not video_path.exists():

        raise FileNotFoundError(
            f"Input video does not exist:\n"
            f"{video_path}"
        )

    if not video_path.is_file():

        raise ValueError(
            f"Input path is not a file:\n"
            f"{video_path}"
        )

    print("=" * 70)
    print("PRAMAANSCAN MULTIMODAL ANALYSIS")
    print("=" * 70)

    print()
    print(
        f"Input video:\n"
        f"{video_path}"
    )

    print()
    print(
        f"Video model: DIVERSE_400"
    )

    print(
        f"Video threshold: 0.45"
    )

    # --------------------------------------------------------
    # Check FFmpeg
    # --------------------------------------------------------

    print()

    if not check_ffmpeg():

        raise RuntimeError(
            "FFmpeg was not found in PATH.\n"
            "Run 'ffmpeg -version' first."
        )

    print("FFmpeg: READY")

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    video_result = (
        analyze_video_component(
            video_path
        )
    )

    # --------------------------------------------------------
    # AUDIO
    # --------------------------------------------------------

    audio_result = (
        analyze_audio(
            video_path
        )
    )

    # --------------------------------------------------------
    # FUSION
    # --------------------------------------------------------

    fusion_result = (
        fuse_results(
            video_result,
            audio_result
        )
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print_final_result(
        video_path,
        video_result,
        audio_result,
        fusion_result
    )

    # --------------------------------------------------------
    # JSON RESULT
    # --------------------------------------------------------

    final_result = {

        "filename":
            video_path.name,

        "media_type":
            "video",

        "video":
            video_result,

        "audio":
            audio_result,

        "multimodal":
            fusion_result
    }

    return final_result


# ============================================================
# COMMAND LINE
# ============================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description=(
            "PramaanScan multimodal "
            "video + audio deepfake analysis"
        )
    )

    parser.add_argument(
        "video",
        help="Path to input video"
    )

    args = parser.parse_args()

    try:

        result = main(
            args.video
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

        print()
        print(str(exc))

        sys.exit(1)