from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.signing_key import SigningKey, KeyStatus
from app.models.revocation import Revocation, RevocationTargetType


def revoke_signing_key(
    db: Session,
    key_id: str,
    reason: str,
    revoked_by: int | None = None,
) -> dict:
    """
    Revoke an active signing key.

    The SigningKey status is updated and an immutable
    Revocation record is created.
    """

    if not reason or not reason.strip():
        raise ValueError("Revocation reason is required.")

    key = (
        db.query(SigningKey)
        .filter(SigningKey.key_id == key_id)
        .first()
    )

    if key is None:
        raise ValueError(f"Signing key '{key_id}' not found.")

    if key.status == KeyStatus.REVOKED:
        raise ValueError(f"Signing key '{key_id}' is already revoked.")

    now = datetime.now(timezone.utc)

    # Update key status
    key.status = KeyStatus.REVOKED
    key.revoked_at = now
    key.revoked_reason = reason.strip()

    # Create durable revocation record
    revocation = Revocation(
        target_type=RevocationTargetType.SIGNING_KEY,
        target_id=key_id,
        reason=reason.strip(),
        revoked_by=revoked_by,
        revoked_at=now,
    )

    db.add(revocation)
    db.commit()
    db.refresh(key)
    db.refresh(revocation)

    return {
        "key_id": key.key_id,
        "status": key.status.value,
        "revoked_at": (
            key.revoked_at.isoformat()
            if key.revoked_at
            else None
        ),
        "reason": key.revoked_reason,
        "revocation_id": revocation.id,
    }


def is_signing_key_revoked(
    db: Session,
    key_id: str,
) -> bool:
    """
    Return True if the signing key is revoked.
    """

    key = (
        db.query(SigningKey)
        .filter(SigningKey.key_id == key_id)
        .first()
    )

    if key is None:
        # Unknown key must never be treated as trusted.
        return True

    return key.status == KeyStatus.REVOKED


def get_signing_key_status(
    db: Session,
    key_id: str,
) -> dict:
    """
    Return the current status of a signing key.
    """

    key = (
        db.query(SigningKey)
        .filter(SigningKey.key_id == key_id)
        .first()
    )

    if key is None:
        return {
            "key_id": key_id,
            "found": False,
            "status": "UNKNOWN",
            "revoked": True,
        }

    return {
        "key_id": key.key_id,
        "found": True,
        "status": key.status.value,
        "revoked": key.status == KeyStatus.REVOKED,
        "algorithm": key.algorithm,
        "created_at": (
            key.created_at.isoformat()
            if key.created_at
            else None
        ),
        "revoked_at": (
            key.revoked_at.isoformat()
            if key.revoked_at
            else None
        ),
        "revoked_reason": key.revoked_reason,
    }
