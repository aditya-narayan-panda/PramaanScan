from __future__ import annotations

import json

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Depends,
)

from sqlalchemy.orm import Session

from app.db.session import get_db

from app.services.hashing import sha256_bytes
from app.services.verification import verify_content
from app.services.media_analysis import (
    analyze_media_bytes,
)

from app.models.communication import (
    CommunicationVersion,
)

from app.models.media_analysis import (
    MediaAnalysis,
    RiskLabel,
)
from app.models.verification_log import VerificationLog, VerificationResult, VerificationSource


router = APIRouter(
    prefix="/verify",
    tags=["Verification"],
)


# ============================================================
# SAVE ML RESULT
# ============================================================

def _store_media_analysis(
    db: Session,
    version: CommunicationVersion,
    result: dict,
):

    risk_score = result.get(
        "risk_score"
    )

    risk_label_text = result.get(
        "risk_label",
        "INCONCLUSIVE",
    )

    try:
        risk_label = RiskLabel(
            risk_label_text
        )

    except ValueError:

        risk_label = (
            RiskLabel.INCONCLUSIVE
        )

    details = json.dumps(
        result,
        default=str,
    )

    analysis = (
        db.query(MediaAnalysis)
        .filter(
            MediaAnalysis.version_id
            == version.id
        )
        .first()
    )

    if analysis is None:

        analysis = MediaAnalysis(
            version_id=version.id,
            risk_score=risk_score,
            risk_label=risk_label,
            model_name=result.get(
                "model_name",
                "PramaanScan Multimodal ML",
            ),
            model_version="1.0",
            details=details,
            is_advisory=True,
        )

        db.add(analysis)

    else:

        analysis.risk_score = risk_score

        analysis.risk_label = risk_label

        analysis.model_name = result.get(
            "model_name",
            "PramaanScan Multimodal ML",
        )

        analysis.model_version = "1.0"

        analysis.details = details

        analysis.is_advisory = True

    db.commit()
    db.refresh(analysis)

    return analysis


# ============================================================
# VERIFY FILE
# ============================================================

@router.post("/file")
async def verify_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="Filename required",
        )

    data = await file.read()

    if not data:

        raise HTTPException(
            status_code=400,
            detail="File is empty",
        )

    # ========================================================
    # 1. CRYPTOGRAPHIC VERIFICATION
    # ========================================================

    digest = sha256_bytes(
        data
    )

    crypto_result = verify_content(
        db=db,
        digest=digest,
        filename=file.filename,
    )

    # ========================================================
    # 2. ML ANALYSIS
    # ========================================================

    ml_result = None
    ml_error = None

    try:

        ml_result = analyze_media_bytes(
            data=data,
            filename=file.filename,
            content_type=(
                file.content_type or ""
            ),
        )

    except Exception as exc:

        ml_error = str(exc)

    # ========================================================
    # 3. FIND REGISTERED VERSION
    # ========================================================

    version = (
        db.query(CommunicationVersion)
        .filter(
            CommunicationVersion.sha256
            == digest
        )
        .first()
    )

    # ========================================================
    # 4. PERSIST ML RESULT
    # ========================================================

    database_result = {
        "stored": False,
    }

    if (
        version is not None
        and ml_result is not None
        and ml_result.get("available", True)
    ):

        try:

            analysis = _store_media_analysis(
                db=db,
                version=version,
                result=ml_result,
            )

            database_result = {
                "stored": True,
                "media_analysis_id": analysis.id,
                "risk_label": (
                    analysis.risk_label.value
                ),
                "risk_score": (
                    analysis.risk_score
                ),
                "model_name": (
                    analysis.model_name
                ),
                "model_version": (
                    analysis.model_version
                ),
                "is_advisory": (
                    analysis.is_advisory
                ),
            }

        except Exception as exc:

            database_result = {
                "stored": False,
                "error": str(exc),
            }

    elif version is None:

        database_result = {
            "stored": False,
            "reason": (
                "No registered communication "
                "version exists for this hash."
            ),
        }

    # ========================================================
    # 5. FINAL RESPONSE
    # ========================================================

    # Append-only verification log. It is deliberately independent of provenance so
    # tampered/unsigned files are also recorded.
    try:
        log_status = crypto_result.get("status", "UNSIGNED")
        try:
            log_result = VerificationResult(log_status)
        except ValueError:
            log_result = VerificationResult.UNSIGNED
        communication_id = crypto_result.get("communication_id")
        db.add(VerificationLog(
            communication_id=communication_id,
            sha256=digest,
            result=log_result,
            source=VerificationSource.FILE_UPLOAD,
        ))
        db.commit()
    except Exception:
        db.rollback()

    response = {
        **crypto_result,

        "cryptographic_verification": {
            "verified": (
                crypto_result.get("status")
                == "VERIFIED"
            ),
            "status": crypto_result.get(
                "status"
            ),
            "sha256": digest,
        },

        "media_analysis": (
            ml_result
            if ml_result is not None
            else {
                "available": False,
                "reason": ml_error,
            }
        ),

        "database": database_result,
    }

    return response

# ============================================================
# QR COMMUNICATION RESOLUTION
# ============================================================

@router.get("/communication/{communication_id}")
def resolve_communication_qr(
    communication_id: str,
    db: Session = Depends(get_db),
):
    """
    Resolve a QR code to the registered communication.

    This endpoint identifies the official communication and its
    current signed version. It does NOT replace cryptographic
    verification.
    """

    version = (
        db.query(CommunicationVersion)
        .join(CommunicationVersion.communication)
        .filter(
            CommunicationVersion.communication.has(
                communication_id=communication_id
            )
        )
        .order_by(
            CommunicationVersion.version_number.desc()
        )
        .first()
    )

    if version is None:
        raise HTTPException(
            status_code=404,
            detail="Communication not found.",
        )

    communication = version.communication
    signing_key = version.signing_key

    return {
        "communication": {
            "communication_id": communication.communication_id,
            "title": communication.title,
            "description": communication.description,
            "category": communication.category,
            "media_type": communication.media_type.value,
            "status": communication.status.value,
            "valid_from": communication.valid_from,
            "valid_until": communication.valid_until,
            "created_at": communication.created_at,
        },
        "current_version": {
            "version": version.version_number,
            "sha256": version.sha256,
            "filename": version.file_name,
            "mime_type": version.mime_type,
            "file_size_bytes": version.file_size_bytes,
            "created_at": version.created_at,
        },
        "signing": {
            "key_id": signing_key.key_id,
            "algorithm": signing_key.algorithm,
            "key_status": signing_key.status.value,
        },
        "qr_verification": {
            "identified": True,
            "message": (
                "Official communication identified. "
                "Use document verification to confirm "
                "cryptographic authenticity."
            ),
        },
    }