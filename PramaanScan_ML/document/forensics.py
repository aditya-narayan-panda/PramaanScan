from __future__ import annotations

from difflib import SequenceMatcher
from io import BytesIO
from pathlib import Path
import re
from typing import Any

from pypdf import PdfReader


def _normalise_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def _page_profile(page: Any) -> dict[str, Any]:
    blocks: list[dict[str, Any]] = []
    fonts: set[str] = set()

    def visitor_text(text, cm, tm, font_dict, font_size):
        value = (text or "").strip()
        if not value:
            return
        font = ""
        if font_dict:
            font = str(font_dict.get("/BaseFont", ""))
        fonts.add(font or "UNKNOWN")
        blocks.append(
            {
                "text": re.sub(r"\s+", " ", value),
                "x": round(float(tm[4]), 1),
                "y": round(float(tm[5]), 1),
                "font": font or "UNKNOWN",
                "size": round(float(font_size or 0), 1),
            }
        )

    try:
        page.extract_text(visitor_text=visitor_text)
    except Exception:
        # Basic extraction remains available even if positional extraction
        # is unsupported by an unusual PDF.
        pass

    resources = page.get("/Resources")
    images = 0
    if resources:
        xobjects = resources.get("/XObject")
        if xobjects:
            for obj in xobjects.values():
                try:
                    if obj.get("/Subtype") == "/Image":
                        images += 1
                except Exception:
                    continue

    return {"blocks": blocks, "fonts": sorted(fonts), "images": images}


def inspect_pdf(data: bytes) -> dict[str, Any]:
    reader = PdfReader(BytesIO(data))
    pages = [_page_profile(page) for page in reader.pages]
    text = "\n\n".join((page.extract_text() or "").strip() for page in reader.pages).strip()

    return {
        "pages": len(reader.pages),
        "text": text,
        "fonts": sorted({font for page in pages for font in page["fonts"]}),
        "images": sum(page["images"] for page in pages),
        "page_profiles": pages,
    }


def compare_reference(reference_data: bytes, candidate_data: bytes) -> dict[str, Any]:
    """Compare a candidate document against a trusted original supplied by the caller.

    This is intentionally not cryptographic. It is a document-forensics comparison
    intended to identify changes that are consistent with editing/tampering.
    """
    reference = inspect_pdf(reference_data)
    candidate = inspect_pdf(candidate_data)

    ref_text = _normalise_text(reference["text"])
    cand_text = _normalise_text(candidate["text"])

    similarity = SequenceMatcher(None, ref_text, cand_text).ratio()
    exact_text_match = ref_text == cand_text

    changed_lines: list[str] = []
    ref_lines = [line.strip() for line in reference["text"].splitlines() if line.strip()]
    cand_lines = [line.strip() for line in candidate["text"].splitlines() if line.strip()]

    import difflib

    for line in difflib.ndiff(ref_lines, cand_lines):
        if line.startswith("- ") or line.startswith("+ "):
            changed_lines.append(line)

    font_changed = reference["fonts"] != candidate["fonts"]
    page_count_changed = reference["pages"] != candidate["pages"]
    image_count_changed = reference["images"] != candidate["images"]

    ref_blocks = [
        (b["text"], round(b["x"], 0), round(b["y"], 0), b["font"], b["size"])
        for p in reference["page_profiles"] for b in p["blocks"]
    ]
    cand_blocks = [
        (b["text"], round(b["x"], 0), round(b["y"], 0), b["font"], b["size"])
        for p in candidate["page_profiles"] for b in p["blocks"]
    ]
    layout_changed = ref_blocks != cand_blocks

    evidence: list[dict[str, str]] = []
    if not exact_text_match:
        evidence.append({
            "type": "TEXT_DIFFERENCE",
            "severity": "HIGH" if similarity < 0.98 else "MEDIUM",
            "detail": f"Extracted text similarity is {similarity * 100:.1f}%.",
        })
    if layout_changed:
        evidence.append({
            "type": "LAYOUT_DIFFERENCE",
            "severity": "MEDIUM",
            "detail": "Text block positions, sizes, fonts, or ordering differ from the supplied reference.",
        })
    if font_changed:
        evidence.append({
            "type": "FONT_DIFFERENCE",
            "severity": "MEDIUM",
            "detail": "The candidate uses a different font set from the supplied reference.",
        })
    if page_count_changed:
        evidence.append({
            "type": "PAGE_COUNT_DIFFERENCE",
            "severity": "HIGH",
            "detail": f"Reference has {reference['pages']} page(s); candidate has {candidate['pages']}.",
        })
    if image_count_changed:
        evidence.append({
            "type": "IMAGE_OBJECT_DIFFERENCE",
            "severity": "MEDIUM",
            "detail": f"Reference has {reference['images']} image object(s); candidate has {candidate['images']}.",
        })

    # High similarity + one or more differences is the strongest controlled
    # tamper signal. A completely different document is not called tampered.
    if exact_text_match and not evidence:
        assessment = "LIKELY_ORIGINAL"
        risk = "LOW"
        score = 0.0
    elif similarity >= 0.85 and evidence:
        assessment = "SUSPICIOUS"
        risk = "HIGH" if (not exact_text_match or page_count_changed) else "MEDIUM"
        score = min(99.0, 70.0 + (1.0 - similarity) * 100.0 + len(evidence) * 5.0)
    else:
        assessment = "REFERENCE_MISMATCH"
        risk = "INCONCLUSIVE"
        score = 50.0

    return {
        "mode": "REFERENCE_FORENSICS",
        "assessment": assessment,
        "tamper_risk": risk,
        "confidence_percent": round(float(score if assessment != "REFERENCE_MISMATCH" else 50.0), 2),
        "reference_text_similarity_percent": round(similarity * 100, 2),
        "exact_text_match": exact_text_match,
        "evidence": evidence,
        "changed_lines": changed_lines[:20],
        "reference": {
            "pages": reference["pages"],
            "fonts": reference["fonts"],
            "images": reference["images"],
        },
        "candidate": {
            "pages": candidate["pages"],
            "fonts": candidate["fonts"],
            "images": candidate["images"],
        },
    }


def standalone_forensics(data: bytes) -> dict[str, Any]:
    """Produce conservative anomaly evidence when no original is supplied.

    Without a trusted reference, this deliberately avoids claiming proof of
    authenticity. It can only report observable document anomalies.
    """
    profile = inspect_pdf(data)
    evidence: list[dict[str, str]] = []

    for index, page in enumerate(profile["page_profiles"], start=1):
        sizes = [b["size"] for b in page["blocks"] if b["size"] > 0]
        if len(sizes) >= 8:
            common = max(set(sizes), key=sizes.count)
            outliers = sum(1 for size in sizes if abs(size - common) >= 4)
            if outliers >= max(3, len(sizes) // 3):
                evidence.append({
                    "type": "FONT_SIZE_ANOMALY",
                    "severity": "LOW",
                    "detail": f"Page {index} contains several font-size outliers.",
                })

        duplicate_positions = len(page["blocks"]) - len({
            (b["text"], round(b["x"], 0), round(b["y"], 0))
            for b in page["blocks"]
        })
        if duplicate_positions:
            evidence.append({
                "type": "DUPLICATE_TEXT_OBJECT",
                "severity": "MEDIUM",
                "detail": f"Page {index} contains overlapping/duplicate text objects.",
            })

    return {
        "mode": "STANDALONE_FORENSICS",
        "assessment": "INCONCLUSIVE" if not evidence else "SUSPICIOUS",
        "tamper_risk": "INCONCLUSIVE" if not evidence else "MEDIUM",
        "confidence_percent": 50.0 if not evidence else 65.0,
        "evidence": evidence,
        "note": "A trusted original/reference is required to establish that a specific edit occurred.",
        "document": {
            "pages": profile["pages"],
            "fonts": profile["fonts"],
            "images": profile["images"],
        },
    }
