import json
import random
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config import (
    TRAIN_REAL,
    TRAIN_FAKE,
    TEST_REAL,
    TEST_FAKE,
    MANIFEST_DIR,
    SEED,
)


# ============================================================
# COLLECT DATASET
# ============================================================

def collect(root, label):

    root = Path(root)

    if not root.exists():

        raise FileNotFoundError(
            f"Dataset directory not found: {root}"
        )

    return [
        {
            "id": p.name,
            "path": str(p),
            "label": label,
        }
        for p in root.iterdir()
        if p.is_dir()
    ]


# ============================================================
# MAIN
# ============================================================

def main():

    rng = random.Random(SEED)

    print("=" * 60)
    print("CREATING BALANCED MANIFESTS")
    print("=" * 60)

    # ========================================================
    # TRAIN DATA
    # ========================================================

    real = collect(
        TRAIN_REAL,
        0
    )

    fake = collect(
        TRAIN_FAKE,
        1
    )

    print(
        "Available REAL train     :",
        len(real)
    )

    print(
        "Available DEEPFAKE train :",
        len(fake)
    )

    if not real or not fake:

        raise SystemExit(
            "Both REAL and DEEPFAKE training directories "
            "must contain samples."
        )

    # ========================================================
    # SHUFFLE BEFORE SPLIT
    # ========================================================

    rng.shuffle(real)
    rng.shuffle(fake)

    # ========================================================
    # BALANCE CLASSES
    # ========================================================

    n = min(
        len(real),
        len(fake)
    )

    real = real[:n]
    fake = fake[:n]

    # ========================================================
    # 80/20 CLASS-WISE SPLIT
    # ========================================================

    val_count = int(
        n * 0.20
    )

    real_val = real[:val_count]
    real_train = real[val_count:]

    fake_val = fake[:val_count]
    fake_train = fake[val_count:]

    train = (
        real_train +
        fake_train
    )

    val = (
        real_val +
        fake_val
    )

    rng.shuffle(train)
    rng.shuffle(val)

    # ========================================================
    # TEST DATA
    #
    # IMPORTANT:
    # We NEVER randomly select a subset here.
    # Every available fixed test sample is included.
    # ========================================================

    test_real = collect(
        TEST_REAL,
        0
    )

    test_fake = collect(
        TEST_FAKE,
        1
    )

    test = (
        test_real +
        test_fake
    )

    rng.shuffle(test)

    # ========================================================
    # SAVE DIRECTORY
    # ========================================================

    MANIFEST_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    manifests = {
        "train": train,
        "val": val,
        "test": test,
    }

    # ========================================================
    # SAVE MANIFESTS
    # ========================================================

    for name, data in manifests.items():

        path = (
            MANIFEST_DIR /
            f"{name}.json"
        )

        path.write_text(
            json.dumps(
                data,
                indent=2
            ),
            encoding="utf-8"
        )

        print(
            f"{name.upper():5} : {len(data)}"
        )

    # ========================================================
    # SUMMARY
    # ========================================================

    print()
    print("=" * 60)
    print("CLASS BALANCE")
    print("=" * 60)

    print(
        "TRAIN REAL     :",
        sum(
            x["label"] == 0
            for x in train
        )
    )

    print(
        "TRAIN DEEPFAKE :",
        sum(
            x["label"] == 1
            for x in train
        )
    )

    print(
        "VAL REAL       :",
        sum(
            x["label"] == 0
            for x in val
        )
    )

    print(
        "VAL DEEPFAKE   :",
        sum(
            x["label"] == 1
            for x in val
        )
    )

    print(
        "TEST REAL      :",
        sum(
            x["label"] == 0
            for x in test
        )
    )

    print(
        "TEST DEEPFAKE  :",
        sum(
            x["label"] == 1
            for x in test
        )
    )

    print()
    print("MANIFESTS CREATED SUCCESSFULLY")


if __name__ == "__main__":
    main()