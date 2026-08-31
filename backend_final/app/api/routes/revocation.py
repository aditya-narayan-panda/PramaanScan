from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.revocation import (
    revoke_signing_key,
    get_signing_key_status,
)
from app.models.signing_key import SigningKey
from app.security.permissions import require_authority_or_admin


router = APIRouter(
    prefix="/revocation",
    tags=["Revocation"],
)


class RevokeKeyRequest(BaseModel):
    key_id: str = Field(
        min_length=1,
        max_length=64,
    )

    reason: str = Field(
        min_length=3,
        max_length=1000,
    )

    revoked_by: int | None = None


@router.post("/key")
def revoke_key(
    request: RevokeKeyRequest,
    db: Session = Depends(get_db),
    payload: dict = Depends(require_authority_or_admin),
):
    """
    Revoke a signing key.
    """

    if payload.get("role") == "AUTHORITY":
        key = db.query(SigningKey).filter(SigningKey.key_id == request.key_id).first()
        if key is None or key.issuer_id != int(payload["issuer_id"]):
            raise HTTPException(status_code=403, detail="You can only revoke keys belonging to your institution.")

    try:

        result = revoke_signing_key(
            db=db,
            key_id=request.key_id,
            reason=request.reason,
            revoked_by=int(payload['sub']),
        )

        return {
            "success": True,
            "message": "Signing key revoked successfully.",
            "revocation": result,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get("/key/{key_id}")
def key_status(
    key_id: str,
    db: Session = Depends(get_db),
    payload: dict = Depends(require_authority_or_admin),
):
    """
    Check whether a signing key is active or revoked.
    """

    if payload.get("role") == "AUTHORITY":
        key = db.query(SigningKey).filter(SigningKey.key_id == key_id).first()
        if key is None or key.issuer_id != int(payload["issuer_id"]):
            raise HTTPException(status_code=403, detail="You can only inspect keys belonging to your institution.")
    return get_signing_key_status(db=db, key_id=key_id)


@router.get("/keys")
def list_signing_keys(
    payload: dict = Depends(require_authority_or_admin),
    db: Session = Depends(get_db),
):
    q = db.query(SigningKey)
    if payload.get("role") == "AUTHORITY":
        q = q.filter(SigningKey.issuer_id == int(payload["issuer_id"]))
    rows = q.order_by(SigningKey.created_at.desc()).all()
    return {
        "items": [
            {
                "id": k.id,
                "key_id": k.key_id,
                "issuer_id": k.issuer_id,
                "algorithm": k.algorithm,
                "status": k.status.value,
                "created_at": k.created_at,
                "revoked_at": k.revoked_at,
                "revoked_reason": k.revoked_reason,
            }
            for k in rows
        ]
    }
