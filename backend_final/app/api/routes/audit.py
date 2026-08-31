import json
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.security.permissions import require_admin

router=APIRouter(prefix="/admin/audit-logs", tags=["Audit"])


@router.get("")
def list_audit_logs(page:int=1,page_size:int=50,action:str|None=None,resource_type:str|None=None,
                    payload:dict=Depends(require_admin),db:Session=Depends(get_db)):
    page=max(page,1); page_size=min(max(page_size,1),100)
    q=db.query(AuditLog)
    if action: q=q.filter(AuditLog.action==action)
    if resource_type: q=q.filter(AuditLog.resource_type==resource_type.upper())
    total=q.count(); rows=q.order_by(AuditLog.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"items":[{"id":r.id,"actor_user_id":r.actor_user_id,"action":r.action,"resource_type":r.resource_type,
                     "resource_id":r.resource_id,"details":json.loads(r.details) if r.details else {},
                     "created_at":r.created_at} for r in rows],
            "page":page,"page_size":page_size,"total":total,"pages":(total+page_size-1)//page_size}
