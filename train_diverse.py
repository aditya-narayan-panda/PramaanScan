from pathlib import Path
import sys

import tensorflow as tf


# ============================================================
# PROJECT SETUP
# ============================================================

ROOT = Path(__file__).resolve().parent

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


from config import *
from src.seed import set_seed
from src.dataset import read_manifest, VideoSequence
from src.face import MediaPipeFaceDetector
from src.model import build_model, unfreeze_backbone


# ============================================================
# DIVERSE TRAINING CONFIGURATION
# ============================================================

# IMPORTANT:
# We intentionally do NOT modify config.py.
#
# This experiment uses:
#
#   manifests/train_diverse.json
#
# instead of:
#
#   manifests/train.json
#
# Validation remains:
#
#   manifests/val.json
#
# Test remains untouched.
#
# The resulting model is saved separately.


DIVERSE_TRAIN_MANIFEST = (
    ROOT / "manifests" / "train_diverse.json"
)

DIVERSE_MODEL_PATH = (
    ROOT
    / "outputs"
    / "models"
    / "DIVERSE_322.keras"
)


# ============================================================
# TRAINING SETTINGS
# ============================================================

DIVERSE_BATCH_SIZE = BATCH_SIZE

DIVERSE_EPOCHS_HEAD = EPOCHS_HEAD

DIVERSE_EPOCHS_FINE = EPOCHS_FINE

DIVERSE_LEARNING_RATE = LEARNING_RATE

DIVERSE_FINE_TUNE_LR = FINE_TUNE_LR


# ============================================================
# SET RANDOM SEED
# ============================================================

set_seed(SEED)


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("PRAMAANSCAN DIVERSE MODEL TRAINING")
print("=" * 70)

print()
print("Training manifest:")
print(DIVERSE_TRAIN_MANIFEST)

print()
print("Validation manifest:")
print(VAL_MANIFEST)

print()
print("Output model:")
print(DIVERSE_MODEL_PATH)


# ============================================================
# CHECK FACE MODEL
# ============================================================

print()
print("=" * 70)
print("CHECKING FACE DETECTOR")
print("=" * 70)


if not FACE_MODEL.exists():

    raise SystemExit(
        "\nFace detector model not found.\n\n"
        "Expected:\n"
        f"{FACE_MODEL}\n\n"
        "Run:\n"
        "python tools/download_face_model.py"
    )


print()
print("Face detector model found:")
print(FACE_MODEL)


# ============================================================
# CHECK DIVERSE MANIFEST
# ============================================================

if not DIVERSE_TRAIN_MANIFEST.exists():

    raise SystemExit(
        "\nDiverse training manifest not found:\n"
        f"{DIVERSE_TRAIN_MANIFEST}\n\n"
        "Run first:\n"
        "python tools/create_diverse_manifest.py"
    )


# ============================================================
# CHECK VALIDATION MANIFEST
# ============================================================

if not VAL_MANIFEST.exists():

    raise SystemExit(
        "\nValidation manifest not found:\n"
        f"{VAL_MANIFEST}"
    )


# ============================================================
# LOAD MANIFESTS
# ============================================================

print()
print("=" * 70)
print("LOADING MANIFESTS")
print("=" * 70)


train = read_manifest(
    DIVERSE_TRAIN_MANIFEST
)

val = read_manifest(
    VAL_MANIFEST
)


print()
print(
    "Diverse training samples :",
    len(train)
)

print(
    "Validation samples       :",
    len(val)
)


# ============================================================
# CLASS DISTRIBUTION
# ============================================================

train_real = sum(
    int(item["label"]) == 0
    for item in train
)

train_fake = sum(
    int(item["label"]) == 1
    for item in train
)

val_real = sum(
    int(item["label"]) == 0
    for item in val
)

val_fake = sum(
    int(item["label"]) == 1
    for item in val
)


print()
print("=" * 70)
print("CLASS DISTRIBUTION")
print("=" * 70)

print()
print(
    "TRAIN REAL     :",
    train_real
)

print(
    "TRAIN DEEPFAKE :",
    train_fake
)

print(
    "VAL REAL       :",
    val_real
)

print(
    "VAL DEEPFAKE   :",
    val_fake
)


# ============================================================
# SANITY CHECK
# ============================================================

if train_real == 0 or train_fake == 0:

    raise SystemExit(
        "\nTraining manifest does not contain both classes."
    )


if val_real == 0 or val_fake == 0:

    raise SystemExit(
        "\nValidation manifest does not contain both classes."
    )


# ============================================================
# VERIFY DIVERSE ENTRIES
# ============================================================

diverse_entries = [

    item
    for item in train
    if str(item["id"]).startswith(
        "diverse_"
    )

]


print()
print("=" * 70)
print("DIVERSE DATA CHECK")
print("=" * 70)


print()
print(
    "Diverse entries found:",
    len(diverse_entries)
)


for item in diverse_entries:

    path = Path(
        item["path"]
    )

    print()
    print(
        "ID    :",
        item["id"]
    )

    print(
        "Label :",
        item["label"]
    )

    print(
        "Path  :",
        path
    )

    if not path.exists():

        raise SystemExit(
            "\nDiverse data path does not exist:\n"
            f"{path}"
        )


    frame_count = len(

        [
            p
            for p in path.iterdir()
            if p.is_file()
            and p.suffix.lower()
            in {
                ".jpg",
                ".jpeg",
                ".png",
                ".bmp",
                ".webp"
            }
        ]

    )


    print(
        "Frames:",
        frame_count
    )


    if frame_count < SEQ_LEN:

        raise SystemExit(
            "\nDiverse sample has fewer than "
            f"{SEQ_LEN} frames:\n"
            f"{path}"
        )


if len(diverse_entries) == 0:

    raise SystemExit(
        "\nNo diverse entries found in "
        "train_diverse.json."
    )


# ============================================================
# FACE DETECTOR
# ============================================================

print()
print("=" * 70)
print("INITIALIZING FACE DETECTOR")
print("=" * 70)


detector = MediaPipeFaceDetector(
    FACE_MODEL
)


print(
    "FACE DETECTOR READY"
)


# ============================================================
# DATA SEQUENCES
# ============================================================

print()
print("=" * 70)
print("CREATING DATA SEQUENCES")
print("=" * 70)


train_seq = VideoSequence(

    train,

    detector,

    batch_size=DIVERSE_BATCH_SIZE,

    training=True,

    shuffle=True
)


val_seq = VideoSequence(

    val,

    detector,

    batch_size=DIVERSE_BATCH_SIZE,

    training=False,

    shuffle=False
)


print()
print(
    "Training batch size:",
    DIVERSE_BATCH_SIZE
)

print(
    "Sequence length:",
    SEQ_LEN
)

print(
    "Image size:",
    IMG_SIZE
)


# ============================================================
# BUILD MODEL
# ============================================================

print()
print("=" * 70)
print("BUILDING PRAMAANSCAN MODEL")
print("=" * 70)


model = build_model()


print()
print(
    "MODEL INPUT :",
    model.input_shape
)

print(
    "MODEL OUTPUT:",
    model.output_shape
)


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

DIVERSE_MODEL_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# COMPILE FUNCTION
# ============================================================

def compile_model(
    model,
    learning_rate,
    label_smoothing=0.02
):

    model.compile(

        optimizer=tf.keras.optimizers.AdamW(

            learning_rate=learning_rate,

            weight_decay=1e-4

        ),

        loss=tf.keras.losses.BinaryCrossentropy(

            label_smoothing=label_smoothing

        ),

        metrics=[

            tf.keras.metrics.BinaryAccuracy(
                name="accuracy"
            ),

            tf.keras.metrics.AUC(
                name="auc",
                curve="ROC"
            ),

            tf.keras.metrics.AUC(
                name="pr_auc",
                curve="PR"
            ),

            tf.keras.metrics.Precision(
                name="precision"
            ),

            tf.keras.metrics.Recall(
                name="recall"
            )

        ]

    )


# ============================================================
# CALLBACKS
# ============================================================

callbacks = [

    tf.keras.callbacks.ModelCheckpoint(

        DIVERSE_MODEL_PATH,

        monitor="val_pr_auc",

        mode="max",

        save_best_only=True,

        verbose=1

    ),

    tf.keras.callbacks.EarlyStopping(

        monitor="val_pr_auc",

        mode="max",

        patience=5,

        min_delta=0.002,

        restore_best_weights=True,

        verbose=1

    ),

    tf.keras.callbacks.ReduceLROnPlateau(

        monitor="val_pr_auc",

        mode="max",

        factor=0.5,

        patience=2,

        min_lr=1e-7,

        verbose=1

    )

]


# ============================================================
# PHASE 1
# FROZEN BACKBONE
# ============================================================

print()
print("=" * 70)
print("PHASE 1")
print("FROZEN EFFICIENTNETV2B0 + TRANSFORMER")
print("=" * 70)


print()
print(
    "Training classification head..."
)

print(
    "Learning rate:",
    DIVERSE_LEARNING_RATE
)

print(
    "Epochs:",
    DIVERSE_EPOCHS_HEAD
)


compile_model(

    model,

    DIVERSE_LEARNING_RATE,

    label_smoothing=0.02

)


history_head = model.fit(

    train_seq,

    validation_data=val_seq,

    epochs=DIVERSE_EPOCHS_HEAD,

    callbacks=callbacks,

    verbose=1

)


# ============================================================
# PHASE 2
# FINE TUNING
# ============================================================

print()
print("=" * 70)
print("PHASE 2")
print("FINE-TUNING EFFICIENTNETV2B0")
print("=" * 70)


print()
print(
    "Unfreezing last 60 backbone layers..."
)


unfreeze_backbone(

    model,

    last_layers=60

)


# ============================================================
# RECOMPILE
# ============================================================

compile_model(

    model,

    DIVERSE_FINE_TUNE_LR,

    label_smoothing=0.01

)


print()
print(
    "Fine-tuning learning rate:",
    DIVERSE_FINE_TUNE_LR
)

print(
    "Fine-tuning epochs:",
    DIVERSE_EPOCHS_FINE
)


history_fine = model.fit(

    train_seq,

    validation_data=val_seq,

    epochs=DIVERSE_EPOCHS_FINE,

    callbacks=callbacks,

    verbose=1

)


# ============================================================
# LOAD BEST CHECKPOINT
# ============================================================

print()
print("=" * 70)
print("LOADING BEST DIVERSE CHECKPOINT")
print("=" * 70)


if DIVERSE_MODEL_PATH.exists():

    best_model = tf.keras.models.load_model(

        DIVERSE_MODEL_PATH,

        safe_mode=False,

        compile=False

    )


    print()
    print(
        "Best diverse checkpoint "
        "loaded successfully."
    )


else:

    best_model = model

    print()
    print(
        "Checkpoint not found."
    )

    print(
        "Using current model."
    )


# ============================================================
# SAVE FINAL DIVERSE MODEL
# ============================================================

best_model.save(
    DIVERSE_MODEL_PATH
)


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 70)
print("PRAMAANSCAN DIVERSE TRAINING COMPLETE")
print("=" * 70)


print()
print(
    "Model saved at:"
)

print(
    DIVERSE_MODEL_PATH
)


print()
print(
    "Training samples:",
    len(train)
)

print(
    "Validation samples:",
    len(val)
)


print()
print("=" * 70)
print("IMPORTANT")
print("=" * 70)

print()
print(
    "Original train.json was NOT modified."
)

print(
    "Original validation set was NOT modified."
)

print(
    "Original test set was NOT modified."
)

print(
    "Original 50/50 model was NOT modified."
)

print()
print(
    "Next step:"
)

print(
    "Evaluate DIVERSE_322.keras "
    "on the untouched test set."
)

print("=" * 70)