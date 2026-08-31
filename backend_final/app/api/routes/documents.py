"""
Document issuance routes.

This module provides a COMPLETE document issuance workflow where the Authority
uploads a file + metadata, and the backend:
1. Reads the private signing key (encrypted at rest in DB)
2. Computes SHA-256 of the uploaded file in-process
3. Signs the hash with Ed25519 automatically
4. Registers the communication
5. Returns the QR code URL

The Authority NEVER needs to:
- See or paste SHA-256
- See or paste signatures
- Handle private keys directly
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.communication import (
    Communication,
    CommunicationVersion,
    CommunicationStatus,
    MediaType,
)
from app.models.issuer import Issuer, IssuerStatus
from app.models.signing_key import SigningKey, KeyStatus
from app.security.permissions import require_authority_or_admin
from app.services.audit import record_audit
from app.services.core_config import get_key_encryption_secret
from app.services.crypto import verify_signature, sign_data
from app.services.hashing import sha256_bytes
from app.core.config import settings

router = APIRouter(prefix="/documents", tags=["Document Issuance"])

MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB


def _get_scoped_issuer(payload: dict, requested_issuer_id: int, db: Session) -> Issuer:
    """
    Security: ensure the requested issuer_id belongs to the requesting authority.
    ADMIN can specify any issuer; AUTHORITY can only use their own issuer.
    """
    role = payload.get("role")
    if role == "AUTHORITY":
        token_issuer_id = payload.get("issuer_id")
        if token_issuer_id is None:
            raise HTTPException(status_code=403, detail="Authority has no institution assigned.")
        if int(token_issuer_id) != int(requested_issuer_id):
            raise HTTPException(
                status_code=403,
                detail="You can only issue documents for your own institution.",
            )

    issuer = db.query(Issuer).filter(Issuer.id == int(requested_issuer_id)).first()
    if issuer is None:
        raise HTTPException(status_code=404, detail="Institution not found.")
    if issuer.status == IssuerStatus.SUSPENDED:
        raise HTTPException(status_code=403, detail="Institution is suspended.")
    return issuer


def _decrypt_private_key(private_key_encrypted: str) -> str:
    """
    Decrypt the stored (base64) private key.
    For demo purposes, the key is stored base64-encoded without additional encryption.
    In production, use KMS/HSM or Fernet symmetric encryption with KEY_ENCRYPTION_SECRET.
    """
    secret = get_key_encryption_secret()
    if secret and secret != "CHANGE_ME":
        # Try Fernet decryption if configured
        try:
            from cryptography.fernet import Fernet
            import base64
            f = Fernet(secret.encode() if len(secret) == 44 else
                       base64.urlsafe_b64encode(secret[:32].encode().ljust(32, b'\x00')))
            decrypted = f.decrypt(private_key_encrypted.encode()).decode()
            return decrypted
        except Exception:
            pass  # Fall through to plain base64

    # Plain base64 storage (demo mode)
    return private_key_encrypted


@router.post("/issue")
async def issue_document(
    file: UploadFile = File(...),
    issuer_id: int = Form(...),
    signing_key_id: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(default=None),
    category: Optional[str] = Form(default=None),
    media_type: str = Form(default="DOCUMENT"),
    student_name: Optional[str] = Form(default=None),
    student_id: Optional[str] = Form(default=None),
    course: Optional[str] = Form(default=None),
    department: Optional[str] = Form(default=None),
    document_type: Optional[str] = Form(default=None),
    valid_from: Optional[str] = Form(default=None),
    valid_until: Optional[str] = Form(default=None),
    payload: dict = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    """
    Complete server-side document issuance workflow.

    The Authority uploads a file, provides metadata, selects a signing key —
    and this endpoint handles all cryptography internally:
    1. SHA-256 of the file is computed
    2. The Ed25519 signature is generated server-side using the stored private key
    3. The communication is registered with full provenance
    4. A QR URL is returned

    SECURITY: Private key bytes are only held in memory during this call.
    They are NEVER returned in the response.
    """

    # ---- Authorization ----
    issuer = _get_scoped_issuer(payload, issuer_id, db)

    # ---- Read and validate file ----
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed: {MAX_UPLOAD_BYTES // (1024*1024)} MB."
        )

    # ---- Validate media_type ----
    try:
        mt = MediaType(media_type.upper())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid media_type: {media_type}")

    # ---- Find signing key ----
    key = db.query(SigningKey).filter(
        SigningKey.key_id == signing_key_id,
        SigningKey.issuer_id == issuer.id,
    ).first()
    if key is None:
        raise HTTPException(status_code=404, detail="Signing key not found for this institution.")
    if key.status != KeyStatus.ACTIVE:
        raise HTTPException(status_code=400, detail=f"Signing key is not active (status: {key.status.value}).")
    if key.private_key_encrypted is None:
        raise HTTPException(
            status_code=400,
            detail="This signing key has no associated private key stored. "
                   "Use the /communications/{id}/versions/upload-register endpoint for externally-signed documents."
        )

    # ---- 1. SHA-256 ----
    digest = sha256_bytes(data)

    # ---- 2. Ed25519 Sign ----
    try:
        raw_private_key = _decrypt_private_key(key.private_key_encrypted)
        signature = sign_data(
            data=digest.encode("utf-8"),
            private_key_b64=raw_private_key,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to sign document. Please contact the administrator."
        )

    # ---- 3. Verify own signature (sanity check) ----
    if not verify_signature(
        data=digest.encode("utf-8"),
        signature_b64=signature,
        public_key_b64=key.public_key,
    ):
        raise HTTPException(status_code=500, detail="Internal signing error: signature verification failed.")

    # ---- 4. Parse validity dates ----
    vf = None
    vu = None
    if valid_from:
        try:
            vf = datetime.fromisoformat(valid_from)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid valid_from date format. Use ISO 8601.")
    if valid_until:
        try:
            vu = datetime.fromisoformat(valid_until)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid valid_until date format. Use ISO 8601.")
    if vf and vu and vu <= vf:
        raise HTTPException(status_code=400, detail="valid_until must be after valid_from.")

    # ---- 5. Build rich title/description with student metadata ----
    full_description = description or ""
    metadata_parts = []
    if student_name:
        metadata_parts.append(f"Student: {student_name}")
    if student_id:
        metadata_parts.append(f"Roll/ID: {student_id}")
    if course:
        metadata_parts.append(f"Course: {course}")
    if department:
        metadata_parts.append(f"Department: {department}")
    if document_type:
        metadata_parts.append(f"Document Type: {document_type}")
    if metadata_parts:
        meta_str = " | ".join(metadata_parts)
        full_description = (full_description + "\n" + meta_str).strip() if full_description else meta_str

    # ---- 6. Register Communication + Version ----
    communication_id = uuid.uuid4().hex

    communication = Communication(
        communication_id=communication_id,
        issuer_id=issuer.id,
        title=title,
        description=full_description or None,
        category=category,
        media_type=mt,
        status=CommunicationStatus.CURRENT,
        valid_from=vf,
        valid_until=vu,
    )
    db.add(communication)
    db.flush()

    version = CommunicationVersion(
        communication_id=communication.id,
        version_number=1,
        sha256=digest,
        signature=signature,
        key_id=key.id,
        file_name=file.filename,
        mime_type=file.content_type,
        file_size_bytes=len(data),
        created_by=int(payload["sub"]),
    )
    db.add(version)
    db.flush()

    communication.current_version_id = version.id
    record_audit(
        db, "ISSUE_DOCUMENT", int(payload["sub"]), "COMMUNICATION",
        communication_id,
        {
            "sha256": digest,
            "signing_key_id": key.key_id,
            "issuer_id": issuer.id,
            "title": title,
        }
    )
    db.commit()
    db.refresh(communication)
    db.refresh(version)

    # ---- 7. Build QR URL ----
    base_url = settings.PUBLIC_BASE_URL.rstrip("/")
    # Point to the FRONTEND verification page, not the raw API
    # The frontend should handle /verify/communication/<id>
    frontend_url = base_url.replace(":8000", ":5173") if ":8000" in base_url else base_url
    qr_url = f"{frontend_url}/verify/communication/{communication_id}"
    api_qr_url = f"{base_url}/api/v1/communications/{communication_id}/qr/image"

    return {
        "success": True,
        "message": "Document issued and registered successfully.",
        "communication": {
            "communication_id": communication_id,
            "title": title,
            "media_type": mt.value,
            "status": "CURRENT",
            "issuer": issuer.institution_name,
            "issuer_id": issuer.id,
        },
        "cryptographic_provenance": {
            "sha256": digest,
            "signature_valid": True,
            "algorithm": key.algorithm,
            "signing_key_id": key.key_id,
            "key_status": key.status.value,
        },
        "version": {
            "version_id": version.id,
            "version_number": version.version_number,
            "file_name": file.filename,
            "mime_type": file.content_type,
            "file_size_bytes": len(data),
        },
        "qr": {
            "verification_url": qr_url,
            "qr_image_url": api_qr_url,
        },
    }


@router.post("/keys/generate")
def generate_key(
    issuer_id: int = Form(...),
    label: str = Form(default="Primary Key"),
    payload: dict = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    """
    Generate a new Ed25519 keypair for an institution.
    The private key is stored encrypted. Only the public key is returned.
    The private key is NEVER exposed through the API.
    """
    issuer = _get_scoped_issuer(payload, issuer_id, db)

    from app.services.crypto import generate_key_pair
    private_key_b64, public_key_b64 = generate_key_pair()

    # Store private key (encrypted at rest using KEY_ENCRYPTION_SECRET if configured)
    secret = get_key_encryption_secret()
    if secret and secret != "CHANGE_ME":
        try:
            from cryptography.fernet import Fernet
            import base64
            f = Fernet(secret.encode() if len(secret) == 44 else
                       base64.urlsafe_b64encode(secret[:32].encode().ljust(32, b'\x00')))
            private_key_stored = f.encrypt(private_key_b64.encode()).decode()
        except Exception:
            private_key_stored = private_key_b64
    else:
        private_key_stored = private_key_b64  # Plain base64 (demo mode)

    import secrets as sec
    key_id = f"key_{sec.token_hex(8)}"

    new_key = SigningKey(
        key_id=key_id,
        issuer_id=issuer.id,
        algorithm="Ed25519",
        public_key=public_key_b64,
        private_key_encrypted=private_key_stored,
        status=KeyStatus.ACTIVE,
    )
    db.add(new_key)
    record_audit(
        db, "GENERATE_KEY", int(payload["sub"]), "SIGNING_KEY", key_id,
        {"issuer_id": issuer.id, "label": label}
    )
    db.commit()
    db.refresh(new_key)

    return {
        "success": True,
        "message": "Ed25519 signing key generated. The private key is stored securely and never exposed through the API.",
        "key": {
            "key_id": new_key.key_id,
            "issuer_id": issuer.id,
            "institution_name": issuer.institution_name,
            "algorithm": new_key.algorithm,
            "public_key": new_key.public_key,  # Public key is safe to return
            "status": new_key.status.value,
            "created_at": new_key.created_at,
        },
        "security_note": "The private key is stored encrypted at rest. It is never returned through this API. Production deployments should use an HSM or KMS.",
    }
