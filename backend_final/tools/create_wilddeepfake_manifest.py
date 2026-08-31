from pathlib import Path
import json
import sys


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# PATHS
# ============================================================

ORIGINAL_MANIFEST = (
    ROOT
    / "manifests"
    / "train.json"
)

OUTPUT_MANIFEST = (
    ROOT
    / "manifests"
    / "train_wilddeepfake.json"
)

DIVERSE_ROOT = (
    ROOT
    / "diverse_frames"
)

REAL_ROOT = (
    DIVERSE_ROOT
    / "real"
)

FAKE_ROOT = (
    DIVERSE_ROOT
    / "fake"
)


# ============================================================
# CONFIG
# ============================================================

FRAMES_PER_SEQUENCE = 16

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
}


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("PRAMAANSCAN WILDDEEPFAKE TRAINING MANIFEST")
print("=" * 70)

print()
print("Project root:")
print(ROOT)

print()
print("Original manifest:")
print(ORIGINAL_MANIFEST)

print()
print("Diverse root:")
print(DIVERSE_ROOT)

print()
print("Output manifest:")
print(OUTPUT_MANIFEST)


# ============================================================
# SAFETY CHECKS
# ============================================================

print()
print("=" * 70)
print("SAFETY CHECKS")
print("=" * 70)


if not ORIGINAL_MANIFEST.exists():

    raise SystemExit(
        "\nERROR: Original train.json not found:\n"
        f"{ORIGINAL_MANIFEST}"
    )


if not REAL_ROOT.exists():

    raise SystemExit(
        "\nERROR: Diverse REAL folder not found:\n"
        f"{REAL_ROOT}"
    )


if not FAKE_ROOT.exists():

    raise SystemExit(
        "\nERROR: Diverse FAKE folder not found:\n"
        f"{FAKE_ROOT}"
    )


print("Original train manifest : FOUND")
print("Diverse REAL directory  : FOUND")
print("Diverse FAKE directory  : FOUND")


# ============================================================
# LOAD ORIGINAL MANIFEST
# ============================================================

print()
print("=" * 70)
print("LOADING ORIGINAL TRAIN MANIFEST")
print("=" * 70)


try:

    with ORIGINAL_MANIFEST.open(
        "r",
        encoding="utf-8"
    ) as f:

        original = json.load(f)

except Exception as e:

    raise SystemExit(
        "\nERROR reading train.json:\n"
        f"{e}"
    )


if not isinstance(original, list):

    raise SystemExit(
        "\nERROR: train.json must contain a JSON list."
    )


print()
print(
    "Original samples:",
    len(original)
)


# ============================================================
# VALIDATE ORIGINAL MANIFEST
# ============================================================

original_ids = set()

original_real = 0
original_fake = 0


for item in original:

    if not isinstance(item, dict):

        raise SystemExit(
            "ERROR: Invalid manifest entry."
        )

    if "id" not in item:
        raise SystemExit(
            "ERROR: Manifest entry missing 'id'."
        )

    if "path" not in item:
        raise SystemExit(
            "ERROR: Manifest entry missing 'path'."
        )

    if "label" not in item:
        raise SystemExit(
            "ERROR: Manifest entry missing 'label'."
        )

    item_id = str(item["id"])

    if item_id in original_ids:

        raise SystemExit(
            f"ERROR: Duplicate original ID: {item_id}"
        )

    original_ids.add(item_id)

    label = int(item["label"])

    if label == 0:

        original_real += 1

    elif label == 1:

        original_fake += 1

    else:

        raise SystemExit(
            f"ERROR: Invalid label {label} "
            f"for {item_id}"
        )


# ============================================================
# FIND DIVERSE SEQUENCES
# ============================================================

def find_sequences(
    root,
    prefix,
    label
):

    if not root.exists():

        return []

    folders = sorted(
        [
            p
            for p in root.iterdir()
            if p.is_dir()
            and p.name.startswith(prefix)
        ],
        key=lambda p: p.name
    )

    results = []

    for folder in folders:

        image_files = sorted(
            [
                p
                for p in folder.iterdir()
                if p.is_file()
                and p.suffix.lower()
                in IMAGE_EXTENSIONS
            ],
            key=lambda p: p.name
        )

        results.append(
            {
                "folder": folder,
                "frames": image_files,
                "label": label,
            }
        )

    return results


# ============================================================
# REAL
# ============================================================

print()
print("=" * 70)
print("PROCESSING WILDDEEPFAKE REAL")
print("=" * 70)


real_sequences = find_sequences(
    REAL_ROOT,
    "wd_real_",
    0
)

print()
print(
    "WildDeepfake REAL folders found:",
    len(real_sequences)
)


# ============================================================
# FAKE
# ============================================================

print()
print("=" * 70)
print("PROCESSING WILDDEEPFAKE FAKE")
print("=" * 70)


fake_sequences = find_sequences(
    FAKE_ROOT,
    "wd_fake_",
    1
)

print()
print(
    "WildDeepfake FAKE folders found:",
    len(fake_sequences)
)


# ============================================================
# VALIDATE DIVERSE DATA
# ============================================================

def validate_sequences(
    sequences,
    class_name
):

    valid = []

    for item in sequences:

        folder = item["folder"]
        frames = item["frames"]

        print()
        print(
            f"{class_name}: {folder.name}"
        )

        print(
            "  Frames:",
            len(frames)
        )

        if len(frames) < FRAMES_PER_SEQUENCE:

            print(
                "  STATUS: SKIP "
                "(not enough frames)"
            )

            continue

        print(
            "  STATUS: READY"
        )

        valid.append(item)

    return valid


print()
print("=" * 70)
print("VALIDATING DIVERSE REAL")
print("=" * 70)

valid_real = validate_sequences(
    real_sequences,
    "REAL"
)


print()
print("=" * 70)
print("VALIDATING DIVERSE FAKE")
print("=" * 70)

valid_fake = validate_sequences(
    fake_sequences,
    "FAKE"
)


# ============================================================
# CREATE NEW MANIFEST
# ============================================================

new_manifest = list(original)

new_ids = set(original_ids)


# ============================================================
# ADD DIVERSE REAL
# ============================================================

added_real = 0
skipped_real = 0


for item in valid_real:

    folder = item["folder"]

    manifest_id = (
        "wilddeepfake_real_"
        + folder.name.replace(
            "wd_real_",
            ""
        )
    )

    if manifest_id in new_ids:

        print(
            "WARNING: Duplicate ID, skipping:",
            manifest_id
        )

        skipped_real += 1

        continue

    new_manifest.append(
        {
            "id": manifest_id,
            "path": str(
                folder.resolve()
            ),
            "label": 0
        }
    )

    new_ids.add(manifest_id)

    added_real += 1


# ============================================================
# ADD DIVERSE FAKE
# ============================================================

added_fake = 0
skipped_fake = 0


for item in valid_fake:

    folder = item["folder"]

    manifest_id = (
        "wilddeepfake_fake_"
        + folder.name.replace(
            "wd_fake_",
            ""
        )
    )

    if manifest_id in new_ids:

        print(
            "WARNING: Duplicate ID, skipping:",
            manifest_id
        )

        skipped_fake += 1

        continue

    new_manifest.append(
        {
            "id": manifest_id,
            "path": str(
                folder.resolve()
            ),
            "label": 1
        }
    )

    new_ids.add(manifest_id)

    added_fake += 1


# ============================================================
# FINAL COUNTS
# ============================================================

final_real = sum(
    int(item["label"]) == 0
    for item in new_manifest
)

final_fake = sum(
    int(item["label"]) == 1
    for item in new_manifest
)


# ============================================================
# BALANCE CHECK
# ============================================================

if final_real != final_fake:

    print()
    print("=" * 70)
    print("WARNING: FINAL DATASET IS NOT PERFECTLY BALANCED")
    print("=" * 70)

    print(
        "REAL:",
        final_real
    )

    print(
        "FAKE:",
        final_fake
    )

else:

    print()
    print("=" * 70)
    print("BALANCE CHECK: PASSED")
    print("=" * 70)

    print(
        "REAL:",
        final_real
    )

    print(
        "FAKE:",
        final_fake
    )


# ============================================================
# WRITE OUTPUT
# ============================================================

OUTPUT_MANIFEST.parent.mkdir(
    parents=True,
    exist_ok=True
)


with OUTPUT_MANIFEST.open(
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        new_manifest,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("WILDDEEPFAKE MANIFEST CREATED")
print("=" * 70)

print()
print("ORIGINAL TRAIN")
print(
    "  REAL  :",
    original_real
)

print(
    "  FAKE  :",
    original_fake
)

print(
    "  TOTAL :",
    len(original)
)


print()
print("WILDDEEPFAKE ADDED")

print(
    "  REAL  :",
    added_real
)

print(
    "  FAKE  :",
    added_fake
)

print(
    "  TOTAL :",
    added_real + added_fake
)


print()
print("SKIPPED")

print(
    "  REAL  :",
    skipped_real
)

print(
    "  FAKE  :",
    skipped_fake
)


print()
print("FINAL TRAINING MANIFEST")

print(
    "  REAL  :",
    final_real
)

print(
    "  FAKE  :",
    final_fake
)

print(
    "  TOTAL :",
    len(new_manifest)
)


print()
print("OUTPUT:")
print(
    OUTPUT_MANIFEST
)


# ============================================================
# SAFETY CONFIRMATION
# ============================================================

print()
print("=" * 70)
print("SAFETY CHECK")
print("=" * 70)

print(
    "train.json      : NOT MODIFIED"
)

print(
    "val.json        : NOT MODIFIED"
)

print(
    "test.json       : NOT MODIFIED"
)

print(
    "Existing models  : NOT MODIFIED"
)

print()
print(
    "Next step:"
)

print(
    "Verify train_wilddeepfake.json before training."
)

print("=" * 70)