from pathlib import Path
import sys

import tensorflow as tf

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from config import *
from src.seed import set_seed
from src.dataset import read_manifest, VideoSequence
from src.face import MediaPipeFaceDetector
from src.model import build_model, unfreeze_backbone


# ============================================================
# SETUP
# ============================================================

set_seed(SEED)

print("=" * 70)
print("PRAMAANSCAN IMPROVED MODEL TRAINING")
print("=" * 70)


# ============================================================
# CHECK FACE MODEL
# ============================================================

if not FACE_MODEL.exists():

    raise SystemExit(
        "Face detector model not found.\n"
        "Run:\n"
        "python tools/download_face_model.py"
    )


# ============================================================
# LOAD MANIFESTS
# ============================================================

train = read_manifest(
    TRAIN_MANIFEST
)

val = read_manifest(
    VAL_MANIFEST
)


print()
print("Training samples   :", len(train))
print("Validation samples :", len(val))


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
        "Training manifest does not contain both classes."
    )

if val_real == 0 or val_fake == 0:

    raise SystemExit(
        "Validation manifest does not contain both classes."
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

print("FACE DETECTOR READY")


# ============================================================
# DATA SEQUENCES
# ============================================================

train_seq = VideoSequence(
    train,
    detector,
    batch_size=BATCH_SIZE,
    training=True,
    shuffle=True
)

val_seq = VideoSequence(
    val,
    detector,
    batch_size=BATCH_SIZE,
    training=False,
    shuffle=False
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
print("MODEL INPUT :", model.input_shape)
print("MODEL OUTPUT:", model.output_shape)


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

MODEL_PATH.parent.mkdir(
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

        MODEL_PATH,

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
print("Training classification head...")
print("Learning rate:", LEARNING_RATE)
print("Epochs       :", EPOCHS_HEAD)

compile_model(
    model,
    LEARNING_RATE,
    label_smoothing=0.02
)

history_head = model.fit(

    train_seq,

    validation_data=val_seq,

    epochs=EPOCHS_HEAD,

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
print("Unfreezing last 60 backbone layers...")

unfreeze_backbone(
    model,
    last_layers=60
)


# ============================================================
# RECOMPILE
# ============================================================

compile_model(
    model,
    FINE_TUNE_LR,
    label_smoothing=0.01
)

print()
print("Fine-tuning learning rate:", FINE_TUNE_LR)
print("Fine-tuning epochs       :", EPOCHS_FINE)


history_fine = model.fit(

    train_seq,

    validation_data=val_seq,

    epochs=EPOCHS_FINE,

    callbacks=callbacks,

    verbose=1
)


# ============================================================
# LOAD BEST CHECKPOINT
# ============================================================

print()
print("=" * 70)
print("LOADING BEST CHECKPOINT")
print("=" * 70)

if MODEL_PATH.exists():

    best_model = tf.keras.models.load_model(
        MODEL_PATH
    )

    print(
        "Best checkpoint loaded successfully."
    )

else:

    best_model = model

    print(
        "Checkpoint not found. "
        "Using current model."
    )


# ============================================================
# SAVE FINAL MODEL
# ============================================================

best_model.save(
    MODEL_PATH
)


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 70)
print("PRAMAANSCAN IMPROVED TRAINING COMPLETE")
print("=" * 70)

print()
print("Model saved at:")
print(MODEL_PATH)

print()
print("IMPORTANT:")
print("Do NOT modify the test set.")
print("Next step: run evaluate_model.py")

print("=" * 70)