from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.communication import CommunicationVersion
from app.models.media_analysis import MediaAnalysis
from app.models.signing_key import SigningKey, KeyStatus
from app.services.crypto import verify_signature


def _get_media_analysis(
    db: Session,
    version: CommunicationVersion,
) -> dict | None:
    """
    Return the stored advisory ML analysis for this communication version.

    AI/media analysis is NEVER used to decide whether a document is
    cryptographically authentic.
    """

    analysis = (
        db.query(MediaAnalysis)
        .filter(
            MediaAnalysis.version_id == version.id
        )
        .first()
    )

    if analysis is None:
        return None

    return {
        "available": True,
        "analysis_id": analysis.id,
        "risk_score": analysis.risk_score,
        "risk_label": analysis.risk_label.value,
        "model_name": analysis.model_name,
        "model_version": analysis.model_version,
        "is_advisory": analysis.is_advisory,
        "details": analysis.details,
    }


def verify_content(
    db: Session,
    digest: str,
    filename: str,
) -> dict:
    """
    Verify an uploaded file against registered provenance.

    Verification order:

    1. Find registered CommunicationVersion using SHA-256.
    2. Check signing key exists.
    3. Check signing key has not been revoked.
    4. Verify Ed25519 digital signature.
    5. If an advisory media analysis exists, attach it.
    6. Return final verification status.

    IMPORTANT:
    Cryptographic verification is authoritative.
    AI/media analysis is secondary advisory evidence only.
    """

    # ---------------------------------------------------------
    # 1. Find registered provenance
    # ---------------------------------------------------------

    version = (
        db.query(CommunicationVersion)
        .filter(
            CommunicationVersion.sha256 == digest
        )
        .first()
    )

    # ---------------------------------------------------------
    # No registered provenance
    # ---------------------------------------------------------

    if version is None:

        return {
            "status": "UNSIGNED",
            "reason": "No trusted registered provenance was found.",
            "sha256": digest,
            "filename": filename,
            "cryptographic_verification": {
                "verified": False,
            },
            "media_analysis": {
                "available": False,
                "reason": "No registered communication version found.",
            },
        }

    # ---------------------------------------------------------
    # 2. Get signing key
    # ---------------------------------------------------------

    signing_key = (
        db.query(SigningKey)
        .filter(
            SigningKey.id == version.key_id
        )
        .first()
    )

    if signing_key is None:

        return {
            "status": "INVALID",
            "reason": "The signing key associated with this communication was not found.",
            "sha256": digest,
            "filename": filename,
            "cryptographic_verification": {
                "verified": False,
            },
            "media_analysis": _get_media_analysis(
                db,
                version,
            ),
        }

    # ---------------------------------------------------------
    # 3. Check revocation
    # ---------------------------------------------------------

    if signing_key.status == KeyStatus.REVOKED:

        return {
            "status": "REVOKED",
            "reason": "The signing credential used for this communication has been revoked.",
            "sha256": digest,
            "filename": filename,
            "key_id": signing_key.key_id,
            "communication_id": version.communication.communication_id,
            "cryptographic_verification": {
                "verified": False,
            },
            "media_analysis": _get_media_analysis(
                db,
                version,
            ),
        }

    # ---------------------------------------------------------
    # 4. Verify Ed25519 signature
    # ---------------------------------------------------------

    signature_valid = verify_signature(
        data=digest.encode("utf-8"),
        signature_b64=version.signature,
        public_key_b64=signing_key.public_key,
    )

    if not signature_valid:

        return {
            "status": "INVALID",
            "reason": "The digital signature is invalid.",
            "sha256": digest,
            "filename": filename,
            "key_id": signing_key.key_id,
            "communication_id": version.communication.communication_id,
            "document_integrity": "MATCH",
            "signature_valid": False,
            "cryptographic_verification": {
                "verified": False,
            },
            "media_analysis": _get_media_analysis(
                db,
                version,
            ),
        }

    # ---------------------------------------------------------
    # 5. Cryptographic verification successful
    # ---------------------------------------------------------

    media_analysis = _get_media_analysis(
        db,
        version,
    )

    # ---------------------------------------------------------
    # 6. Final response
    # ---------------------------------------------------------

    return {
        "status": "VERIFIED",
        "reason": "Document hash and Ed25519 digital signature are valid.",

        "communication_id": version.communication.communication_id,
        "version": version.version_number,

        "sha256": digest,
        "filename": filename,

        "key_id": signing_key.key_id,
        "algorithm": signing_key.algorithm,
        "key_status": signing_key.status.value,

        "document_integrity": "MATCH",
        "signature_valid": True,

        "cryptographic_verification": {
            "verified": True,
            "algorithm": signing_key.algorithm,
            "key_status": signing_key.status.value,
        },

        "media_analysis": (
            media_analysis
            if media_analysis is not None
            else {
                "available": False,
                "reason": "No advisory media analysis has been registered for this version.",
            }
        ),
    }