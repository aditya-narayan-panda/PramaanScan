from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import get_db
from app.models.communication import Communication
from app.security.permissions import require_authority_or_admin
from app.services.qr import generate_qr_bytes, generate_qr_data

router=APIRouter(prefix="/communications",tags=["QR"])


@router.get("/{communication_id}/qr")
def qr_data(communication_id:str,db:Session=Depends(get_db),payload:dict=Depends(require_authority_or_admin)):
    c=db.query(Communication).filter(Communication.communication_id==communication_id).first()
    if not c: raise HTTPException(status_code=404,detail="Communication not found.")
    if payload.get("role")=="AUTHORITY" and c.issuer_id!=int(payload["issuer_id"]):
        raise HTTPException(status_code=403,detail="You can only access your institution's communication.")
    return generate_qr_data(communication_id, settings.FRONTEND_BASE_URL)


@router.get("/{communication_id}/qr/image")
def qr_image(communication_id:str,db:Session=Depends(get_db)):
    """Public endpoint — QR image can be fetched by anyone (it's printed on documents)."""
    c=db.query(Communication).filter(Communication.communication_id==communication_id).first()
    if not c: raise HTTPException(status_code=404,detail="Communication not found.")
    return Response(generate_qr_bytes(communication_id, settings.FRONTEND_BASE_URL),media_type="image/png")
