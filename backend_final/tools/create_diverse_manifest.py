from pathlib import Path
import json
import sys


# ============================================================
# PRAMAANSCAN DIVERSE TRAINING MANIFEST
# ============================================================
#
# Creates:
#
#     manifests/train_diverse.json
#
# WITHOUT modifying:
#
#     manifests/train.json
#     manifests/val.json
#     manifests/test.json
#     any trained model
#
#
# Existing training data:
#     train.json = 320 samples
#
# Diverse data:
#     diverse_frames/real/real_001/
#     diverse_frames/fake/fake_001/
#
# The existing VideoSequence expects each manifest item's
# "path" to be a directory containing image frames.
#
# Therefore we simply add the diverse frame directories
# as normal manifest entries.
# ============================================================


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# PATHS
# ============================================================

MANIFEST_DIR = ROOT / "manifests"

ORIGINAL_TRAIN = (
    MANIFEST_DIR / "train.json"
)

DIVERSE_ROOT = (
    ROOT / "diverse_frames"
)

DIVERSE_REAL = (
    DIVERSE_ROOT / "real"
)

DIVERSE_FAKE = (
    DIVERSE_ROOT / "fake"
)

OUTPUT_MANIFEST = (
    MANIFEST_DIR / "train_diverse.json"
)


# ============================================================
# SETTINGS
# ============================================================

MIN_FRAMES = 16

VALID_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


# ============================================================
# HEADER
# ============================================================

print("=" * 70)
print("PRAMAANSCAN DIVERSE TRAINING MANIFEST")
print("=" * 70)

print()
print("Project root:")
print(ROOT)

print()
print("Original manifest:")
print(ORIGINAL_TRAIN)

print()
print("Diverse root:")
print(DIVERSE_ROOT)

print()
print("Output manifest:")
print(OUTPUT_MANIFEST)


# ============================================================
# CHECK ORIGINAL MANIFEST
# ============================================================

if not ORIGINAL_TRAIN.exists():

    raise SystemExit(
        "\nERROR: Original train.json not found:\n"
        f"{ORIGINAL_TRAIN}"
    )


# ============================================================
# CHECK DIVERSE ROOT
# ============================================================

if not DIVERSE_ROOT.exists():

    raise SystemExit(
        "\nERROR: diverse_frames directory not found:\n"
        f"{DIVERSE_ROOT}"
    )


# ============================================================
# LOAD ORIGINAL TRAIN MANIFEST
# ============================================================

print()
print("=" * 70)
print("LOADING ORIGINAL TRAIN MANIFEST")
print("=" * 70)

with open(
    ORIGINAL_TRAIN,
    "r",
    encoding="utf-8"
) as f:

    original_train = json.load(f)


if not isinstance(
    original_train,
    list
):

    raise SystemExit(
        "\nERROR: train.json must contain a JSON list."
    )


print(
    "\nOriginal samples:",
    len(original_train)
)


# ============================================================
# VALIDATE ORIGINAL ENTRIES
# ============================================================

for index, item in enumerate(
    original_train
):

    if not isinstance(
        item,
        dict
    ):

        raise SystemExit(
            f"\nERROR: Invalid entry at index {index}."
        )

    if "id" not in item:

        raise SystemExit(
            f"\nERROR: Entry {index} "
            "does not contain 'id'."
        )

    if "path" not in item:

        raise SystemExit(
            f"\nERROR: Entry {index} "
            "does not contain 'path'."
        )

    if "label" not in item:

        raise SystemExit(
            f"\nERROR: Entry {index} "
            "does not contain 'label'."
        )


# ============================================================
# FRAME DISCOVERY
# ============================================================

def get_frames(folder):

    if not folder.exists():

        return []

    frames = []

    for path in folder.iterdir():

        if not path.is_file():
            continue

        if path.suffix.lower() not in VALID_EXTENSIONS:
            continue

        frames.append(path)

    # Natural-ish sorting.
    #
    # frame_1.jpg
    # frame_2.jpg
    # frame_10.jpg
    #
    # rather than alphabetical ordering.

    def sort_key(path):

        digits = ""

        for char in path.stem:

            if char.isdigit():
                digits += char

        if digits:

            return (
                0,
                int(digits),
                path.name.lower()
            )

        return (
            1,
            0,
            path.name.lower()
        )

    frames.sort(
        key=sort_key
    )

    return frames


# ============================================================
# PROCESS DIVERSE CLASS
# ============================================================

def process_diverse_class(
    root,
    label,
    class_name
):

    print()
    print("=" * 70)
    print(
        f"PROCESSING DIVERSE {class_name}"
    )
    print("=" * 70)

    if not root.exists():

        print(
            "Folder does not exist:"
        )

        print(root)

        return []


    video_dirs = [

        p
        for p in root.iterdir()
        if p.is_dir()

    ]

    video_dirs.sort(
        key=lambda p: p.name.lower()
    )


    print(
        "Folders found:",
        len(video_dirs)
    )


    entries = []


    for index, folder in enumerate(
        video_dirs,
        start=1
    ):

        print()
        print(
            f"[{index}/{len(video_dirs)}]"
        )

        print(
            "Folder:",
            folder.name
        )


        frames = get_frames(
            folder
        )


        print(
            "Frames:",
            len(frames)
        )


        # ----------------------------------------------------
        # Minimum sequence check
        # ----------------------------------------------------

        if len(frames) < MIN_FRAMES:

            print(
                "STATUS: SKIPPED"
            )

            print(
                f"Reason: fewer than "
                f"{MIN_FRAMES} frames."
            )

            continue


        # ----------------------------------------------------
        # Verify frame readability
        # ----------------------------------------------------

        readable_frames = 0

        for frame in frames:

            try:

                if frame.exists():

                    readable_frames += 1

            except Exception:

                pass


        if readable_frames < MIN_FRAMES:

            print(
                "STATUS: SKIPPED"
            )

            print(
                "Reason: insufficient readable frames."
            )

            continue


        # ----------------------------------------------------
        # Create manifest entry
        # ----------------------------------------------------

        entry_id = (
            f"diverse_"
            f"{class_name.lower()}_"
            f"{folder.name}"
        )


        entry = {

            "id": entry_id,

            "path": str(
                folder.resolve()
            ),

            "label": int(label)

        }


        entries.append(
            entry
        )


        print(
            "STATUS: READY"
        )

        print(
            "Label:",
            label
        )

        print(
            "Path:",
            folder.resolve()
        )


    return entries


# ============================================================
# REAL
# ============================================================

diverse_real_entries = (
    process_diverse_class(
        DIVERSE_REAL,
        label=0,
        class_name="REAL"
    )
)


# ============================================================
# FAKE
# ============================================================

diverse_fake_entries = (
    process_diverse_class(
        DIVERSE_FAKE,
        label=1,
        class_name="FAKE"
    )
)


# ============================================================
# COMBINE
# ============================================================

diverse_entries = (
    diverse_real_entries +
    diverse_fake_entries
)


new_train = (
    original_train +
    diverse_entries
)


# ============================================================
# CLASS COUNTS
# ============================================================

original_real = sum(
    int(item["label"]) == 0
    for item in original_train
)

original_fake = sum(
    int(item["label"]) == 1
    for item in original_train
)


diverse_real = sum(
    int(item["label"]) == 0
    for item in diverse_entries
)

diverse_fake = sum(
    int(item["label"]) == 1
    for item in diverse_entries
)


final_real = sum(
    int(item["label"]) == 0
    for item in new_train
)

final_fake = sum(
    int(item["label"]) == 1
    for item in new_train
)


# ============================================================
# DUPLICATE ID CHECK
# ============================================================

ids = [
    item["id"]
    for item in new_train
]

duplicate_ids = (
    len(ids) != len(set(ids))
)


if duplicate_ids:

    raise SystemExit(
        "\nERROR: Duplicate IDs detected."
    )


# ============================================================
# SAVE
# ============================================================

MANIFEST_DIR.mkdir(
    parents=True,
    exist_ok=True
)


with open(
    OUTPUT_MANIFEST,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        new_train,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# FINAL REPORT
# ============================================================

print()
print("=" * 70)
print("DIVERSE MANIFEST CREATED")
print("=" * 70)

print()
print("ORIGINAL TRAIN")
print(
    f"  REAL  : {original_real}"
)
print(
    f"  FAKE  : {original_fake}"
)
print(
    f"  TOTAL : {len(original_train)}"
)


print()
print("DIVERSE DATA ADDED")
print(
    f"  REAL  : {diverse_real}"
)
print(
    f"  FAKE  : {diverse_fake}"
)
print(
    f"  TOTAL : {len(diverse_entries)}"
)


print()
print("NEW TRAINING MANIFEST")
print(
    f"  REAL  : {final_real}"
)
print(
    f"  FAKE  : {final_fake}"
)
print(
    f"  TOTAL : {len(new_train)}"
)


print()
print("OUTPUT:")
print(
    OUTPUT_MANIFEST
)


print()
print("=" * 70)
print("SAFETY CHECK")
print("=" * 70)

print()
print("train.json      : NOT MODIFIED")
print("val.json        : NOT MODIFIED")
print("test.json       : NOT MODIFIED")
print("Existing model  : NOT MODIFIED")


print()
print(
    "Next step: verify train_diverse.json "
    "before training."
)

print("=" * 70)