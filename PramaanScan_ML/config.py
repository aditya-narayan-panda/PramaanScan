import os
from pathlib import Path

# Training dataset root. Only used by training/evaluation/tooling
# scripts (train.py, evaluate_model.py, backend_final/tools/*) —
# NOT by the runtime inference path (predict_video_v4.py,
# predict_multimodal.py, image_ml prediction service), which was
# verified not to reference DATA_ROOT. Configurable via the
# PRAMAANSCAN_DATA_ROOT env var so this is portable across
# machines instead of pointing at one developer's Windows folder.
DATA_ROOT = Path(
    os.environ.get(
        "PRAMAANSCAN_DATA_ROOT",
        str(Path(__file__).resolve().parent / "data"),
    )
)

TRAIN_REAL = DATA_ROOT / "train" / "real"
TRAIN_FAKE = DATA_ROOT / "train" / "fake"
TEST_REAL = DATA_ROOT / "test" / "real"
TEST_FAKE = DATA_ROOT / "test" / "fake"

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "outputs"
MANIFEST_DIR = ROOT / "manifests"
MODEL_DIR = OUTPUT_DIR / "models"

IMG_SIZE = 224
SEQ_LEN = 16
FACE_MARGIN = 0.30
MIN_DETECTION_SCORE = 0.50

SEED = 42
BATCH_SIZE = 2
EPOCHS_HEAD = 8
EPOCHS_FINE = 12
LEARNING_RATE = 1e-4
FINE_TUNE_LR = 2e-5

TRANSFORMER_DIM = 256
NUM_HEADS = 4
TRANSFORMER_DROPOUT = 0.20
NUM_TRANSFORMER_BLOCKS = 2
DENSE_DROPOUT = 0.35

FACE_MODEL = ROOT / "models" / "face_detector.tflite"
FACE_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"

TRAIN_MANIFEST = MANIFEST_DIR / "train.json"
VAL_MANIFEST = MANIFEST_DIR / "val.json"
TEST_MANIFEST = MANIFEST_DIR / "test.json"

MODEL_PATH = MODEL_DIR / "OLD_50_50_RECOVERED.keras"
