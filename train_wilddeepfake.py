from pathlib import Path
import sys
import tensorflow as tf


# ============================================================
# SETUP
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
# CONFIG FOR FAST WILDDEEPFAKE TRAINING
# ============================================================

TRAIN_MANIFEST_WD = (
    ROOT
    / "manifests"
    / "train_wilddeepfake.json"
)

OUTPUT_MODEL = (
    ROOT
    / "outputs"
    / "models"
    / "DIVERSE_400.keras"
)

FAST_BATCH_SIZE = 2

PHASE1_EPOCHS = 4
PHASE2_EPOCHS = 6

PHASE1_LR = 1e-4
PHASE2_LR = 2e-5

FINE_TUNE_LAYERS = 40


# ============================================================
# HEADER
# ============================================================

set_seed(SEED)

print("=" * 70)
print("PRAMAANSCAN WILDDEEPFAKE FAST TRAINING")
print("=" * 70)

print()
print("Training manifest:")
print(TRAIN_MANIFEST_WD)

print()
print("Output model:")
print(OUTPUT_MODEL)

print()
print("Maximum epochs:")
print(PHASE1_EPOCHS + PHASE2_EPOCHS)

print()
print("IMPORTANT:")
print("Original train.json will NOT be modified.")
print("val.json will NOT be modified.")
print("test.json will NOT be modified.")
print("Existing models will NOT be modified.")


# ============================================================
# SAFETY CHECK
# ============================================================

if not TRAIN_MANIFEST_WD.exists():

    raise SystemExit(
        "\nERROR: train_wilddeepfake.json not found.\n"
        "Run first:\n"
        "python tools\\create_wilddeepfake_manifest.py"
    )


if not FACE_MODEL.exists():

    raise SystemExit(
        "\nERROR: Face detector model not found.\n"
        "Run:\n"
        "python tools\\download_face_model.py"
    )


# ============================================================
# LOAD MANIFEST
# ============================================================

print()
print("=" * 70)
print("LOADING WILDDEEPFAKE TRAINING MANIFEST")
print("=" * 70)

train = read_manifest(
    TRAIN_MANIFEST_WD
)

print()
print(
    "Training samples:",
    len(train)
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


print()
print("=" * 70)
print("CLASS DISTRIBUTION")
print("=" * 70)

print(
    "REAL     :",
    train_real
)

print(
    "DEEPFAKE :",
    train_fake
)

print(
    "TOTAL    :",
    len(train)
)


if train_real == 0 or train_fake == 0:

    raise SystemExit(
        "\nERROR: Both REAL and DEEPFAKE classes are required."
    )


if train_real != train_fake:

    print()
    print(
        "WARNING: Dataset is not perfectly balanced."
    )


# ============================================================
# VALIDATE SAMPLE PATHS
# ============================================================

print()
print("=" * 70)
print("VALIDATING TRAINING PATHS")
print("=" * 70)

missing = []

for i, item in enumerate(train):

    path = Path(
        item["path"]
    )

    if not path.exists():

        missing.append(
            (
                item["id"],
                str(path)
            )
        )

    if len(missing) >= 10:
        break


if missing:

    print()

    for item_id, path in missing:

        print(
            "MISSING:",
            item_id,
            "->",
            path
        )

    raise SystemExit(
        "\nERROR: Missing training paths."
    )


print(
    "All training paths: OK"
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
# TRAINING SEQUENCE
# ============================================================

print()
print("=" * 70)
print("CREATING TRAINING SEQUENCE")
print("=" * 70)

train_seq = VideoSequence(
    train,
    detector,
    batch_size=FAST_BATCH_SIZE,
    training=True,
    shuffle=True
)

print(
    "Training sequence created."
)

print(
    "Batch size:",
    FAST_BATCH_SIZE
)


# ============================================================
# BUILD MODEL
# ============================================================

print()
print("=" * 70)
print("BUILDING MODEL")
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

OUTPUT_MODEL.parent.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# COMPILE FUNCTION
# ============================================================

def compile_model(
    model,
    learning_rate,
    label_smoothing
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

        filepath=OUTPUT_MODEL,

        monitor="loss",

        mode="min",

        save_best_only=True,

        verbose=1
    ),

    tf.keras.callbacks.EarlyStopping(

        monitor="loss",

        mode="min",

        patience=2,

        min_delta=0.001,

        restore_best_weights=True,

        verbose=1
    ),

    tf.keras.callbacks.ReduceLROnPlateau(

        monitor="loss",

        mode="min",

        factor=0.5,

        patience=1,

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
print("PHASE 1: FAST HEAD TRAINING")
print("=" * 70)

print()
print(
    "Epochs       :",
    PHASE1_EPOCHS
)

print(
    "Learning rate:",
    PHASE1_LR
)

print(
    "Backbone     : FROZEN"
)


compile_model(
    model,
    PHASE1_LR,
    label_smoothing=0.02
)


history1 = model.fit(

    train_seq,

    epochs=PHASE1_EPOCHS,

    callbacks=callbacks,

    verbose=1
)


# ============================================================
# PHASE 2
# FINE TUNING
# ============================================================

print()
print("=" * 70)
print("PHASE 2: FAST FINE-TUNING")
print("=" * 70)

print()
print(
    "Unfreezing last",
    FINE_TUNE_LAYERS,
    "backbone layers..."
)


unfreeze_backbone(
    model,
    last_layers=FINE_TUNE_LAYERS
)


compile_model(
    model,
    PHASE2_LR,
    label_smoothing=0.01
)


print()
print(
    "Epochs       :",
    PHASE2_EPOCHS
)

print(
    "Learning rate:",
    PHASE2_LR
)


history2 = model.fit(

    train_seq,

    epochs=PHASE2_EPOCHS,

    callbacks=callbacks,

    verbose=1
)


# ============================================================
# LOAD BEST MODEL
# ============================================================

print()
print("=" * 70)
print("LOADING BEST CHECKPOINT")
print("=" * 70)


if OUTPUT_MODEL.exists():

    best_model = tf.keras.models.load_model(
        OUTPUT_MODEL,
        safe_mode=False,
        compile=False
    )

    print(
        "Best checkpoint loaded successfully."
    )

else:

    best_model = model

    print(
        "Checkpoint not found."
    )

    print(
        "Using current model."
    )


# ============================================================
# FINAL SAVE
# ============================================================

best_model.save(
    OUTPUT_MODEL
)


# ============================================================
# COMPLETE
# ============================================================

print()
print("=" * 70)
print("WILDDEEPFAKE FAST TRAINING COMPLETE")
print("=" * 70)

print()
print("Training data:")
print(
    "REAL     :",
    train_real
)

print(
    "DEEPFAKE :",
    train_fake
)

print(
    "TOTAL    :",
    len(train)
)

print()
print("Model saved at:")
print(
    OUTPUT_MODEL
)

print()
print("Next step:")
print(
    "Run evaluate_diverse.py after updating it "
    "to use DIVERSE_400.keras."
)

print("=" * 70)