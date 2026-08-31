from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.verification_log import VerificationLog
from app.security.permissions import require_authority_or_admin

router=APIRouter(prefix="/verification/logs", tags=["Verification Logs"])


@router.get("")
def list_logs(page:int=1,page_size:int=50,result:str|None=None,source:str|None=None,
              communication_id:str|None=None,payload:dict=Depends(require_authority_or_admin),db:Session=Depends(get_db)):
    page=max(page,1); page_size=min(max(page_size,1),100)
    q=db.query(VerificationLog)
    if result: q=q.filter(VerificationLog.result==result.upper())
    if source: q=q.filter(VerificationLog.source==source.upper())
    if communication_id: q=q.filter(VerificationLog.communication_id==communication_id)
    if payload.get("role")=="AUTHORITY" and payload.get("issuer_id") is not None:
        from app.models.communication import Communication
        q=q.join(Communication, Communication.communication_id==VerificationLog.communication_id).filter(
            Communication.issuer_id==int(payload["issuer_id"]))
    total=q.count(); rows=q.order_by(VerificationLog.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"items":[{"id":r.id,"communication_id":r.communication_id,"sha256":r.sha256,"result":r.result.value,
                     "source":r.source.value,"created_at":r.created_at} for r in rows],
            "page":page,"page_size":page_size,"total":total,"pages":(total+page_size-1)//page_size}


@router.get("/{log_id}")
def get_log(log_id:int,payload:dict=Depends(require_authority_or_admin),db:Session=Depends(get_db)):
    r=db.query(VerificationLog).filter(VerificationLog.id==log_id).first()
    if not r: raise HTTPException(status_code=404,detail="Verification log not found.")
    return {"id":r.id,"communication_id":r.communication_id,"sha256":r.sha256,"result":r.result.value,
            "source":r.source.value,"created_at":r.created_at}
