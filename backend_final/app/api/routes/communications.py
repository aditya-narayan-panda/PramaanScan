from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from app.schemas.communication import CommunicationCreate #added

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from app.security.permissions import require_authority_or_admin

from app.db.session import get_db
from app.models.communication import (
    Communication,
    CommunicationVersion,
    CommunicationStatus,
    MediaType,
)
from app.models.issuer import Issuer
from app.models.signing_key import SigningKey, KeyStatus
from app.services.crypto import verify_signature


router = APIRouter(
    prefix="/communications",
    tags=["Communications"],
)


# ============================================================
# SCHEMAS
# ============================================================

class RegisterCommunicationRequest(BaseModel):
    """
    Register an already-signed official communication.

    IMPORTANT:
    The private signing key is NEVER sent to this API.
    The trusted signing process happens outside this endpoint.
    """

    issuer_id: int = Field(gt=0)

    title: str = Field(
        min_length=1,
        max_length=500,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    category: str | None = Field(
        default=None,
        max_length=64,
    )

    media_type: MediaType

    sha256: str = Field(
        min_length=64,
        max_length=64,
    )

    signature: str = Field(
        min_length=1,
        max_length=10000,
    )

    signing_key_id: str = Field(
        min_length=1,
        max_length=64,
    )

    file_name: str | None = Field(
        default=None,
        max_length=255,
    )

    mime_type: str | None = Field(
        default=None,
        max_length=128,
    )

    file_size_bytes: int | None = Field(
        default=None,
        ge=0,
    )

    valid_from: datetime | None = None

    valid_until: datetime | None = None


# ============================================================
# HELPERS
# ============================================================

def _validate_sha256(value: str) -> str:
    """
    Ensure SHA-256 is exactly 64 hexadecimal characters.
    """

    value = value.strip().lower()

    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise HTTPException(
            status_code=400,
            detail="sha256 must be a valid 64-character hexadecimal SHA-256 hash.",
        )

    return value


def _serialize_version(
    version: CommunicationVersion,
) -> dict:
    communication = version.communication
    signing_key = version.signing_key

    return {
        "version_id": version.id,
        "communication_id": communication.communication_id,
        "version": version.version_number,
        "title": communication.title,
        "description": communication.description,
        "category": communication.category,
        "media_type": communication.media_type.value,
        "communication_status": communication.status.value,
        "sha256": version.sha256,
        "signature": version.signature,
        "signing_key_id": signing_key.key_id,
        "algorithm": signing_key.algorithm,
        "key_status": signing_key.status.value,
        "file_name": version.file_name,
        "mime_type": version.mime_type,
        "file_size_bytes": version.file_size_bytes,
        "valid_from": communication.valid_from,
        "valid_until": communication.valid_until,
        "created_at": version.created_at,
    }


# ============================================================
# CREATE / REGISTER COMMUNICATION
# ============================================================

@router.post("")
def register_communication(
    request: RegisterCommunicationRequest,
    db: Session = Depends(get_db),
):
    """
    Register an officially signed communication.

    Flow:

        Issuer
          ↓
        Signing Key
          ↓
        SHA-256 + Ed25519 signature
          ↓
        Cryptographic validation
          ↓
        Communication + Version stored
    """

    digest = _validate_sha256(request.sha256)

    # --------------------------------------------------------
    # Validate validity period
    # --------------------------------------------------------

    if request.valid_from and request.valid_until:
        if request.valid_until <= request.valid_from:
            raise HTTPException(
                status_code=400,
                detail="valid_until must be later than valid_from.",
            )

    # --------------------------------------------------------
    # Find issuer
    # --------------------------------------------------------

    issuer = (
        db.query(Issuer)
        .filter(Issuer.id == request.issuer_id)
        .first()
    )

    if issuer is None:
        raise HTTPException(
            status_code=404,
            detail="Issuer not found.",
        )

    # --------------------------------------------------------
    # Find signing key
    # --------------------------------------------------------

    signing_key = (
        db.query(SigningKey)
        .filter(
            SigningKey.key_id == request.signing_key_id,
            SigningKey.issuer_id == issuer.id,
        )
        .first()
    )

    if signing_key is None:
        raise HTTPException(
            status_code=404,
            detail="Signing key not found for this issuer.",
        )

    # --------------------------------------------------------
    # Key must currently be trusted
    # --------------------------------------------------------

    if signing_key.status != KeyStatus.ACTIVE:
        raise HTTPException(
            status_code=400,
            detail=(
                "The signing key is not active. "
                f"Current status: {signing_key.status.value}"
            ),
        )

    # --------------------------------------------------------
    # Verify Ed25519 signature BEFORE storing provenance
    # --------------------------------------------------------

    signature_valid = verify_signature(
        data=digest.encode("utf-8"),
        signature_b64=request.signature,
        public_key_b64=signing_key.public_key,
    )

    if not signature_valid:
        raise HTTPException(
            status_code=400,
            detail="Invalid Ed25519 signature. Communication was not registered.",
        )

    # --------------------------------------------------------
    # Generate unique communication ID
    # --------------------------------------------------------

    communication_id = uuid.uuid4().hex

    communication = Communication(
        communication_id=communication_id,
        issuer_id=issuer.id,
        title=request.title,
        description=request.description,
        category=request.category,
        media_type=request.media_type,
        status=CommunicationStatus.CURRENT,
        valid_from=request.valid_from,
        valid_until=request.valid_until,
    )

    db.add(communication)
    db.flush()

    # --------------------------------------------------------
    # First version
    # --------------------------------------------------------

    version = CommunicationVersion(
        communication_id=communication.id,
        version_number=1,
        sha256=digest,
        signature=request.signature,
        key_id=signing_key.id,
        file_name=request.file_name,
        mime_type=request.mime_type,
        file_size_bytes=request.file_size_bytes,
    )

    db.add(version)
    db.flush()

    communication.current_version_id = version.id

    db.commit()

    db.refresh(communication)
    db.refresh(version)

    return {
        "success": True,
        "message": "Signed communication registered successfully.",
        "communication": {
            "communication_id": communication.communication_id,
            "issuer_id": issuer.id,
            "institution_name": issuer.institution_name,
            "title": communication.title,
            "media_type": communication.media_type.value,
            "status": communication.status.value,
            "current_version": version.version_number,
        },
        "cryptographic_provenance": {
            "sha256": version.sha256,
            "signature_valid": True,
            "algorithm": signing_key.algorithm,
            "signing_key_id": signing_key.key_id,
            "key_status": signing_key.status.value,
        },
        "version": {
            "version_id": version.id,
            "version_number": version.version_number,
            "file_name": version.file_name,
            "mime_type": version.mime_type,
            "file_size_bytes": version.file_size_bytes,
        },
    }


# ============================================================
# GET COMMUNICATION / PROVENANCE
# ============================================================

@router.get("/{communication_id}")
def get_communication(
    communication_id: str,
    db: Session = Depends(get_db),
):
    """
    Public provenance lookup using Communication ID.
    """

    communication = (
        db.query(Communication)
        .filter(
            Communication.communication_id == communication_id
        )
        .first()
    )

    if communication is None:
        raise HTTPException(
            status_code=404,
            detail="Communication not found.",
        )

    issuer = communication.issuer

    versions = (
        db.query(CommunicationVersion)
        .filter(
            CommunicationVersion.communication_id == communication.id
        )
        .order_by(
            CommunicationVersion.version_number
        )
        .all()
    )

    return {
        "communication_id": communication.communication_id,
        "issuer": {
            "issuer_id": issuer.id,
            "institution_name": issuer.institution_name,
            "email": issuer.email,
        },
        "title": communication.title,
        "description": communication.description,
        "category": communication.category,
        "media_type": communication.media_type.value,
        "status": communication.status.value,
        "current_version_id": communication.current_version_id,
        "valid_from": communication.valid_from,
        "valid_until": communication.valid_until,
        "versions": [
            _serialize_version(version)
            for version in versions
        ],
    }


# ============================================================
# GET VERSION HISTORY
# ============================================================

@router.get("/{communication_id}/versions")
def get_version_history(
    communication_id: str,
    db: Session = Depends(get_db),
):
    """
    Return complete immutable version history.
    """

    communication = (
        db.query(Communication)
        .filter(
            Communication.communication_id == communication_id
        )
        .first()
    )

    if communication is None:
        raise HTTPException(
            status_code=404,
            detail="Communication not found.",
        )

    versions = (
        db.query(CommunicationVersion)
        .filter(
            CommunicationVersion.communication_id == communication.id
        )
        .order_by(
            CommunicationVersion.version_number
        )
        .all()
    )

    return {
        "communication_id": communication.communication_id,
        "current_version_id": communication.current_version_id,
        "current_status": communication.status.value,
        "total_versions": len(versions),
        "versions": [
            _serialize_version(version)
            for version in versions
        ],
    }


# ============================================================
# GET CURRENT VERSION
# ============================================================

@router.get("/{communication_id}/current")
def get_current_version(
    communication_id: str,
    db: Session = Depends(get_db),
):
    """
    Return the currently active version of a communication.
    """

    communication = (
        db.query(Communication)
        .filter(
            Communication.communication_id == communication_id
        )
        .first()
    )

    if communication is None:
        raise HTTPException(
            status_code=404,
            detail="Communication not found.",
        )

    if communication.current_version is None:
        raise HTTPException(
            status_code=404,
            detail="Communication has no current version.",
        )

    return _serialize_version(
        communication.current_version
    )


# ============================================================
# CREATE DRAFT COMMUNICATION
# ============================================================

@router.post("/draft")
def create_draft(
    request: CommunicationCreate,
    payload: dict = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    issuer_id = payload.get("issuer_id")
    if payload.get("role") == "AUTHORITY":
        if issuer_id is None:
            raise HTTPException(status_code=403, detail="Authority has no issuer assigned.")
    else:
        issuer_id = issuer_id or None
        if issuer_id is None:
            raise HTTPException(status_code=400, detail="ADMIN must provide issuer_id for a draft.")

    issuer = db.query(Issuer).filter(Issuer.id == int(issuer_id)).first()
    if issuer is None:
        raise HTTPException(status_code=404, detail="Issuer not found.")
    if request.valid_from and request.valid_until and request.valid_until <= request.valid_from:
        raise HTTPException(status_code=400, detail="valid_until must be later than valid_from.")

    c = Communication(
        communication_id=uuid.uuid4().hex,
        issuer_id=issuer.id,
        title=request.title,
        description=request.description,
        category=request.category,
        media_type=request.media_type,
        status=CommunicationStatus.CURRENT,
        valid_from=request.valid_from,
        valid_until=request.valid_until,
    )
    db.add(c)
    record_audit(db, "CREATE_COMMUNICATION_DRAFT", int(payload["sub"]), "COMMUNICATION", c.communication_id)
    db.commit()
    db.refresh(c)
    return {
        "success": True,
        "communication_id": c.communication_id,
        "issuer_id": c.issuer_id,
        "title": c.title,
        "media_type": c.media_type.value,
        "status": c.status.value,
    }


# ============================================================
# FRONTEND-FACING DOCUMENT APIs
# ============================================================

from fastapi import UploadFile, File, Form
from app.schemas.communication import CommunicationUpdate, CommunicationCreate
from app.security.permissions import require_authority_or_admin
from app.services.hashing import sha256_bytes
from app.services.crypto import verify_signature
from app.services.audit import record_audit


def _scope_communication(query, payload):
    if payload.get("role") == "AUTHORITY" and payload.get("issuer_id") is not None:
        query = query.filter(Communication.issuer_id == int(payload["issuer_id"]))
    return query


@router.get("")
def list_communications(
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    status: str | None = None,
    media_type: MediaType | None = None,
    category: str | None = None,
    payload: dict = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    q = _scope_communication(db.query(Communication), payload)
    if search:
        term = f"%{search.strip()}%"
        q = q.filter(Communication.title.ilike(term))
    if status:
        q = q.filter(Communication.status == status.upper())
    if media_type:
        q = q.filter(Communication.media_type == media_type)
    if category:
        q = q.filter(Communication.category == category)
    total = q.count()
    items = q.order_by(Communication.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "items": [{
            "id": c.id,
            "communication_id": c.communication_id,
            "issuer_id": c.issuer_id,
            "title": c.title,
            "description": c.description,
            "category": c.category,
            "media_type": c.media_type.value,
            "status": c.status.value,
            "current_version_id": c.current_version_id,
            "valid_from": c.valid_from,
            "valid_until": c.valid_until,
            "created_at": c.created_at,
        } for c in items],
        "page": page,
        "page_size": page_size,
        "total": total,
        "pages": (total + page_size - 1) // page_size,
    }


@router.put("/{communication_id}")
def update_communication(
    communication_id: str,
    request: CommunicationUpdate,
    payload: dict = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    c = db.query(Communication).filter(Communication.communication_id == communication_id).first()
    if c is None:
        raise HTTPException(status_code=404, detail="Communication not found.")
    if payload.get("role") == "AUTHORITY" and c.issuer_id != int(payload["issuer_id"]):
        raise HTTPException(status_code=403, detail="You can only modify your institution's communications.")
    if request.title is not None: c.title = request.title
    if request.description is not None: c.description = request.description
    if request.category is not None: c.category = request.category
    if request.status is not None:
        try: c.status = CommunicationStatus(request.status.upper())
        except ValueError: raise HTTPException(status_code=400, detail="Invalid communication status.")
    if request.valid_from is not None: c.valid_from = request.valid_from
    if request.valid_until is not None: c.valid_until = request.valid_until
    record_audit(db, "UPDATE_COMMUNICATION", int(payload["sub"]), "COMMUNICATION", c.communication_id)
    db.commit()
    db.refresh(c)
    return {"success": True, "communication_id": c.communication_id, "status": c.status.value}


@router.delete("/{communication_id}")
def delete_communication(
    communication_id: str,
    payload: dict = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    c = db.query(Communication).filter(Communication.communication_id == communication_id).first()
    if c is None:
        raise HTTPException(status_code=404, detail="Communication not found.")
    if payload.get("role") == "AUTHORITY" and c.issuer_id != int(payload["issuer_id"]):
        raise HTTPException(status_code=403, detail="You can only modify your institution's communications.")
    c.status = CommunicationStatus.REVOKED
    record_audit(db, "DELETE_COMMUNICATION", int(payload["sub"]), "COMMUNICATION", c.communication_id)
    db.commit()
    return {"success": True, "message": "Communication archived/revoked.", "communication_id": c.communication_id}


@router.post("/{communication_id}/versions/upload-register")
async def upload_and_register_version(
    communication_id: str,
    file: UploadFile = File(...),
    signing_key_id: str = Form(...),
    signature: str = Form(...),
    payload: dict = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    c = db.query(Communication).filter(Communication.communication_id == communication_id).first()
    if c is None: raise HTTPException(status_code=404, detail="Communication not found.")
    if payload.get("role") == "AUTHORITY" and c.issuer_id != int(payload["issuer_id"]):
        raise HTTPException(status_code=403, detail="You can only modify your institution's communications.")
    data = await file.read()
    if not data: raise HTTPException(status_code=400, detail="File is empty.")
    key = db.query(SigningKey).filter(SigningKey.key_id == signing_key_id, SigningKey.issuer_id == c.issuer_id).first()
    if key is None: raise HTTPException(status_code=404, detail="Signing key not found.")
    if key.status != KeyStatus.ACTIVE: raise HTTPException(status_code=400, detail="Signing key is not active.")
    digest = sha256_bytes(data)
    if not verify_signature(digest.encode("utf-8"), signature, key.public_key):
        raise HTTPException(status_code=400, detail="Invalid Ed25519 signature.")
    next_version = max([v.version_number for v in c.versions] or [0]) + 1
    v = CommunicationVersion(
        communication_id=c.id, version_number=next_version, sha256=digest,
        signature=signature, key_id=key.id, file_name=file.filename,
        mime_type=file.content_type, file_size_bytes=len(data),
        created_by=int(payload["sub"]),
    )
    db.add(v)
    if c.current_version_id:
        c.status = CommunicationStatus.SUPERSEDED
    db.flush()
    c.current_version_id = v.id
    c.status = CommunicationStatus.CURRENT
    record_audit(db, "UPLOAD_SIGNED_VERSION", int(payload["sub"]), "COMMUNICATION", c.communication_id,
                 {"version": next_version, "sha256": digest})
    db.commit()
    db.refresh(v)
    return {"success": True, "communication_id": c.communication_id, "version_id": v.id,
            "version": next_version, "sha256": digest, "signature_valid": True}
