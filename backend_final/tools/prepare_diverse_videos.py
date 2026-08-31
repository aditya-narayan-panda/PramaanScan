from pathlib import Path
import sys
import cv2
import numpy as np

# ============================================================
# PATH SETUP
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

DIVERSE_ROOT = ROOT / "diverse_videos"
OUTPUT_ROOT = ROOT / "diverse_frames"

REAL_INPUT = DIVERSE_ROOT / "real"
FAKE_INPUT = DIVERSE_ROOT / "fake"

REAL_OUTPUT = OUTPUT_ROOT / "real"
FAKE_OUTPUT = OUTPUT_ROOT / "fake"

# ============================================================
# SETTINGS
# ============================================================

FRAMES_PER_VIDEO = 32

IMG_SIZE = 224

VIDEO_EXTENSIONS = {
    ".mp4",
    ".avi",
    ".mov",
    ".mkv",
    ".webm",
    ".m4v",
}

MIN_FACE_RATIO = 0.50

FACE_MARGIN = 0.30

# ============================================================
# IMPORT PROJECT FACE DETECTOR
# ============================================================

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from config import FACE_MODEL
    from src.face import MediaPipeFaceDetector
except Exception as e:
    print()
    print("=" * 70)
    print("ERROR: COULD NOT LOAD PROJECT FACE DETECTOR")
    print("=" * 70)
    print()
    print(e)
    print()
    print("Make sure you are running this from the project")
    print("virtual environment and that src/face.py exists.")
    sys.exit(1)


# ============================================================
# UTILITY
# ============================================================

def print_header(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# VIDEO LIST
# ============================================================

def get_videos(folder):
    if not folder.exists():
        return []

    videos = []

    for path in sorted(folder.iterdir()):
        if (
            path.is_file()
            and path.suffix.lower() in VIDEO_EXTENSIONS
        ):
            videos.append(path)

    return videos


# ============================================================
# FRAME INDICES
# ============================================================

def sample_indices(total_frames, count):
    if total_frames <= 0:
        return []

    if total_frames <= count:
        return np.linspace(
            0,
            total_frames - 1,
            total_frames,
            dtype=int,
        ).tolist()

    indices = np.linspace(
        0,
        total_frames - 1,
        count,
    )

    return np.round(indices).astype(int).tolist()


# ============================================================
# OPEN VIDEO
# ============================================================

def open_video(path):
    cap = cv2.VideoCapture(str(path))

    if not cap.isOpened():
        return None

    total = int(
        cap.get(cv2.CAP_PROP_FRAME_COUNT)
    )

    fps = float(
        cap.get(cv2.CAP_PROP_FPS)
        or 0.0
    )

    if fps <= 0:
        fps = 30.0

    return cap, total, fps


# ============================================================
# READ SPECIFIC FRAME
# ============================================================

def read_frame(cap, index):

    cap.set(
        cv2.CAP_PROP_POS_FRAMES,
        index
    )

    ok, frame = cap.read()

    if not ok or frame is None:
        return None

    return frame


# ============================================================
# FACE CROP
# ============================================================

def extract_face(detector, frame):

    if frame is None:
        return None, 0.0

    try:

        # OpenCV BGR -> RGB
        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        face, detection_score = detector.crop(
            rgb,
            FACE_MARGIN
        )

        if face is None:
            return None, 0.0

        face = np.asarray(face)

        if face.size == 0:
            return None, 0.0

        # Resize
        face = cv2.resize(
            face,
            (
                IMG_SIZE,
                IMG_SIZE
            ),
            interpolation=cv2.INTER_AREA
        )

        # RGB -> BGR for cv2.imwrite
        face = cv2.cvtColor(
            face,
            cv2.COLOR_RGB2BGR
        )

        return face, float(detection_score)

    except Exception:
        return None, 0.0


# ============================================================
# PROCESS ONE VIDEO
# ============================================================

def process_video(
    video_path,
    output_class_dir,
    detector,
    class_name,
):

    print()
    print("-" * 70)
    print("VIDEO:", video_path.name)
    print("CLASS:", class_name)

    opened = open_video(video_path)

    if opened is None:
        print("STATUS: FAILED TO OPEN")
        return {
            "success": False,
            "faces": 0,
            "frames": 0,
        }

    cap, total_frames, fps = opened

    if total_frames <= 0:
        cap.release()

        print("STATUS: INVALID VIDEO")
        return {
            "success": False,
            "faces": 0,
            "frames": 0,
        }

    indices = sample_indices(
        total_frames,
        FRAMES_PER_VIDEO
    )

    # Unique output directory for this video
    video_id = video_path.stem

    output_dir = (
        output_class_dir
        / video_id
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    successful_faces = 0
    saved_frames = 0

    qualities = []

    for frame_number, index in enumerate(indices):

        frame = read_frame(
            cap,
            index
        )

        face, detection_score = extract_face(
            detector,
            frame
        )

        if face is None:

            print(
                f"  Frame {frame_number + 1:02d}/{len(indices):02d}"
                f" -> NO FACE"
            )

            continue

        output_file = (
            output_dir
            / f"frame_{frame_number:04d}.jpg"
        )

        ok = cv2.imwrite(
            str(output_file),
            face,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                95
            ]
        )

        if ok:

            successful_faces += 1
            saved_frames += 1
            qualities.append(
                detection_score
            )

            print(
                f"  Frame {frame_number + 1:02d}/{len(indices):02d}"
                f" -> FACE"
                f" | score {detection_score:.3f}"
            )

    cap.release()

    face_ratio = (
        successful_faces / len(indices)
        if len(indices) > 0
        else 0.0
    )

    mean_quality = (
        float(np.mean(qualities))
        if qualities
        else 0.0
    )

    print()
    print(
        f"Frames selected : {len(indices)}"
    )

    print(
        f"Faces detected  : "
        f"{successful_faces}/{len(indices)}"
    )

    print(
        f"Face ratio      : "
        f"{face_ratio * 100:.1f}%"
    )

    print(
        f"Mean quality    : "
        f"{mean_quality:.3f}"
    )

    if face_ratio < MIN_FACE_RATIO:

        print(
            "STATUS          : LOW QUALITY / SKIPPED"
        )

        return {
            "success": False,
            "faces": successful_faces,
            "frames": len(indices),
        }

    print(
        "STATUS          : READY"
    )

    return {
        "success": True,
        "faces": successful_faces,
        "frames": len(indices),
    }


# ============================================================
# PROCESS CLASS
# ============================================================

def process_class(
    input_dir,
    output_dir,
    class_name,
    detector,
):

    print_header(
        f"PROCESSING {class_name.upper()} VIDEOS"
    )

    videos = get_videos(
        input_dir
    )

    print(
        "Input folder:",
        input_dir
    )

    print(
        "Videos found:",
        len(videos)
    )

    if len(videos) == 0:

        print()
        print(
            "WARNING: No videos found."
        )

        return {
            "videos": 0,
            "successful": 0,
            "failed": 0,
        }

    successful = 0
    failed = 0

    for number, video in enumerate(
        videos,
        start=1
    ):

        print()
        print(
            f"[{number}/{len(videos)}]"
        )

        result = process_video(
            video,
            output_dir,
            detector,
            class_name,
        )

        if result["success"]:
            successful += 1
        else:
            failed += 1

    return {
        "videos": len(videos),
        "successful": successful,
        "failed": failed,
    }


# ============================================================
# MAIN
# ============================================================

def main():

    print_header(
        "PRAMAANSCAN DIVERSE DATA PREPARATION"
    )

    print()
    print(
        "Project root:",
        ROOT
    )

    print(
        "Input root  :",
        DIVERSE_ROOT
    )

    print(
        "Output root :",
        OUTPUT_ROOT
    )

    print()
    print(
        "Frames/video:",
        FRAMES_PER_VIDEO
    )

    print(
        "Face size   :",
        IMG_SIZE,
        "x",
        IMG_SIZE
    )

    print(
        "Face margin :",
        FACE_MARGIN
    )

    print()
    print(
        "IMPORTANT:"
    )

    print(
        "Original videos will NOT be modified."
    )

    print(
        "Existing test data will NOT be modified."
    )

    print(
        "Existing trained models will NOT be modified."
    )

    # --------------------------------------------------------
    # CHECK INPUT DIRECTORIES
    # --------------------------------------------------------

    if not REAL_INPUT.exists():

        raise SystemExit(
            f"\nReal video folder not found:\n"
            f"{REAL_INPUT}"
        )

    if not FAKE_INPUT.exists():

        raise SystemExit(
            f"\nFake video folder not found:\n"
            f"{FAKE_INPUT}"
        )

    # --------------------------------------------------------
    # CREATE OUTPUT DIRECTORIES
    # --------------------------------------------------------

    REAL_OUTPUT.mkdir(
        parents=True,
        exist_ok=True
    )

    FAKE_OUTPUT.mkdir(
        parents=True,
        exist_ok=True
    )

    # --------------------------------------------------------
    # CHECK FACE MODEL
    # --------------------------------------------------------

    if not FACE_MODEL.exists():

        raise SystemExit(
            "\nFace detector model not found:\n"
            f"{FACE_MODEL}\n\n"
            "Run:\n"
            "python tools\\download_face_model.py"
        )

    # --------------------------------------------------------
    # INITIALIZE DETECTOR
    # --------------------------------------------------------

    print_header(
        "INITIALIZING FACE DETECTOR"
    )

    detector = MediaPipeFaceDetector(
        FACE_MODEL
    )

    print(
        "FACE DETECTOR READY"
    )

    # --------------------------------------------------------
    # PROCESS REAL
    # --------------------------------------------------------

    real_stats = process_class(
        REAL_INPUT,
        REAL_OUTPUT,
        "REAL",
        detector,
    )

    # --------------------------------------------------------
    # PROCESS FAKE
    # --------------------------------------------------------

    fake_stats = process_class(
        FAKE_INPUT,
        FAKE_OUTPUT,
        "FAKE",
        detector,
    )

    # --------------------------------------------------------
    # FINAL SUMMARY
    # --------------------------------------------------------

    print_header(
        "DIVERSE DATA PREPARATION COMPLETE"
    )

    print()
    print(
        "REAL VIDEOS"
    )

    print(
        "  Found     :",
        real_stats["videos"]
    )

    print(
        "  Successful:",
        real_stats["successful"]
    )

    print(
        "  Failed    :",
        real_stats["failed"]
    )

    print()
    print(
        "FAKE VIDEOS"
    )

    print(
        "  Found     :",
        fake_stats["videos"]
    )

    print(
        "  Successful:",
        fake_stats["successful"]
    )

    print(
        "  Failed    :",
        fake_stats["failed"]
    )

    print()
    print(
        "Output:"
    )

    print(
        REAL_OUTPUT
    )

    print(
        FAKE_OUTPUT
    )

    print()
    print(
        "=" * 70
    )

    print(
        "NEXT STEP:"
    )

    print(
        "Do NOT train yet."
    )

    print(
        "Send me this output first."
    )

    print(
        "=" * 70
    )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()