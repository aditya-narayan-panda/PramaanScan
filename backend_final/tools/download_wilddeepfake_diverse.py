from pathlib import Path
import sys
import tarfile
import shutil
import random

from huggingface_hub import hf_hub_download


# ============================================================
# CONFIG
# ============================================================

ROOT = Path(__file__).resolve().parent.parent

OUTPUT_ROOT = ROOT / "diverse_frames"

REAL_OUTPUT = OUTPUT_ROOT / "real"
FAKE_OUTPUT = OUTPUT_ROOT / "fake"

CACHE_ROOT = ROOT / "_wilddeepfake_cache"

REPO_ID = "xingjunm/WildDeepfake"

TARGET_REAL = 40
TARGET_FAKE = 40

FRAMES_PER_SEQUENCE = 16

SEED = 42


# ============================================================
# SETUP
# ============================================================

random.seed(SEED)

REAL_OUTPUT.mkdir(parents=True, exist_ok=True)
FAKE_OUTPUT.mkdir(parents=True, exist_ok=True)

CACHE_ROOT.mkdir(parents=True, exist_ok=True)


print("=" * 70)
print("PRAMAANSCAN WILDDEEPFAKE DIVERSE DATA PREPARATION")
print("=" * 70)

print()
print("Project root :", ROOT)
print("Repository   :", REPO_ID)

print()
print("Target:")
print("  REAL :", TARGET_REAL)
print("  FAKE :", TARGET_FAKE)

print()
print("Frames per sequence:", FRAMES_PER_SEQUENCE)

print()
print("IMPORTANT:")
print("Existing diverse data will NOT be overwritten.")
print("Existing train/val/test manifests will NOT be modified.")
print("Existing models will NOT be modified.")


# ============================================================
# HELPERS
# ============================================================

def get_existing_ids(output_dir, prefix):
    """
    Find already-created WildDeepfake sequence folders.
    """

    ids = set()

    for p in output_dir.glob(f"{prefix}_*"):

        if p.is_dir():
            ids.add(p.name)

    return ids


def get_png_members(tar):
    """
    Return PNG members only.
    """

    return [
        m
        for m in tar.getmembers()
        if m.isfile()
        and m.name.lower().endswith(".png")
    ]


def group_sequences(members):
    """
    Group PNG files by sequence directory.

    Expected structure:

    ./1/fake/131/frame.png

    Therefore sequence key is:

    131
    """

    groups = {}

    for member in members:

        parts = member.name.replace("\\", "/").split("/")

        if len(parts) < 5:
            continue

        sequence_id = parts[3]

        if sequence_id in (".", ""):
            continue

        groups.setdefault(sequence_id, []).append(member)

    return groups


def select_frames(members, count):
    """
    Select evenly spaced frames from a sequence.

    We sort using the filename stem where possible.
    """

    def frame_key(member):

        name = Path(member.name).stem

        try:
            return int(name)

        except ValueError:
            return name

    members = sorted(
        members,
        key=frame_key
    )

    if len(members) < count:
        return None

    if len(members) == count:
        return members

    # Evenly spaced selection
    indices = [
        round(
            i * (len(members) - 1) / (count - 1)
        )
        for i in range(count)
    ]

    return [
        members[i]
        for i in indices
    ]


def safe_extract_sequence(
    tar,
    selected_members,
    output_dir,
    label_prefix,
    sequence_number
):
    """
    Extract selected frames into:

    wd_real_001/
        frame_0001.png
        ...
        frame_0016.png
    """

    folder_name = (
        f"wd_{label_prefix}_{sequence_number:03d}"
    )

    destination = output_dir / folder_name

    if destination.exists():
        print(
            f"SKIP existing: {destination.name}"
        )
        return False

    destination.mkdir(
        parents=True,
        exist_ok=False
    )

    try:

        for index, member in enumerate(
            selected_members,
            start=1
        ):

            source = tar.extractfile(member)

            if source is None:
                raise RuntimeError(
                    f"Could not read {member.name}"
                )

            output_file = (
                destination
                / f"frame_{index:04d}.png"
            )

            with output_file.open("wb") as f:
                shutil.copyfileobj(
                    source,
                    f
                )

        return True

    except Exception:

        shutil.rmtree(
            destination,
            ignore_errors=True
        )

        return False


def process_class(
    archive_numbers,
    class_name,
    output_dir,
    target_count
):

    print()
    print("=" * 70)
    print(
        f"PROCESSING {class_name.upper()} WILDDEEPFAKE"
    )
    print("=" * 70)

    existing = get_existing_ids(
        output_dir,
        f"wd_{class_name.lower()}"
    )

    print(
        "Existing WildDeepfake sequences:",
        len(existing)
    )

    created = len(existing)

    if created >= target_count:

        print(
            f"Already have {created} "
            f"{class_name} sequences."
        )

        return created

    for archive_number in archive_numbers:

        if created >= target_count:
            break

        split_name = (
            "real_train"
            if class_name.lower() == "real"
            else "fake_train"
        )

        repo_path = (
            f"deepfake_in_the_wild/"
            f"{split_name}/"
            f"{archive_number}.tar.gz"
        )

        print()
        print("-" * 70)
        print("Archive:", repo_path)

        try:

            local_path = hf_hub_download(
                repo_id=REPO_ID,
                filename=repo_path,
                repo_type="dataset",
                cache_dir=str(CACHE_ROOT)
            )

        except Exception as e:

            print(
                "DOWNLOAD FAILED:",
                repr(e)
            )

            continue

        print(
            "Downloaded/cache:",
            local_path
        )

        try:

            # IMPORTANT:
            # WildDeepfake files are TAR archives
            # despite the .tar.gz filename.
            tar = tarfile.open(
                local_path,
                mode="r:"
            )

        except Exception as e:

            print(
                "ARCHIVE OPEN FAILED:",
                repr(e)
            )

            continue

        try:

            members = get_png_members(tar)

            print(
                "PNG frames:",
                len(members)
            )

            groups = group_sequences(
                members
            )

            print(
                "Sequences found:",
                len(groups)
            )

            sequence_items = list(
                groups.items()
            )

            random.shuffle(
                sequence_items
            )

            for sequence_id, sequence_members in sequence_items:

                if created >= target_count:
                    break

                if len(sequence_members) < FRAMES_PER_SEQUENCE:
                    continue

                selected = select_frames(
                    sequence_members,
                    FRAMES_PER_SEQUENCE
                )

                if selected is None:
                    continue

                created += 1

                success = safe_extract_sequence(
                    tar,
                    selected,
                    output_dir,
                    class_name.lower(),
                    created
                )

                if not success:
                    created -= 1
                    continue

                print(
                    f"  CREATED "
                    f"{class_name.upper()} "
                    f"{created:03d} "
                    f"(source sequence {sequence_id}, "
                    f"{len(sequence_members)} frames)"
                )

        finally:

            tar.close()

    print()
    print(
        f"{class_name.upper()} TOTAL:",
        created
    )

    return created


# ============================================================
# ARCHIVE SELECTION
# ============================================================

# We start with a deterministic spread rather than
# downloading the first 8 archives only.

REAL_ARCHIVES = [
    1, 11, 21, 31, 41, 51, 61, 71,
    81, 91, 101, 111
]

FAKE_ARCHIVES = [
    1, 11, 21, 31, 41, 51, 61, 71,
    81, 91, 101, 111
]


# ============================================================
# PROCESS
# ============================================================

real_count = process_class(
    REAL_ARCHIVES,
    "REAL",
    REAL_OUTPUT,
    TARGET_REAL
)

fake_count = process_class(
    FAKE_ARCHIVES,
    "FAKE",
    FAKE_OUTPUT,
    TARGET_FAKE
)


# ============================================================
# FINAL SUMMARY
# ============================================================

print()
print("=" * 70)
print("WILDDEEPFAKE DIVERSE PREPARATION COMPLETE")
print("=" * 70)

print()
print("REAL sequences created :", real_count)
print("FAKE sequences created :", fake_count)

print()
print("REAL output:")
print(REAL_OUTPUT)

print()
print("FAKE output:")
print(FAKE_OUTPUT)

print()
print("=" * 70)

if (
    real_count >= TARGET_REAL
    and fake_count >= TARGET_FAKE
):

    print("STATUS: READY")
    print()
    print(
        "Next step:"
    )
    print(
        "Create the diverse manifest."
    )

else:

    print("STATUS: INCOMPLETE")
    print()
    print(
        "More WildDeepfake archives are needed."
    )

print("=" * 70)