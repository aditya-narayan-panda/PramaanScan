from collections import Counter
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.communication import Communication, CommunicationVersion
from app.models.media_analysis import MediaAnalysis
from app.models.verification_log import VerificationLog
from app.security.permissions import require_authority_or_admin

router=APIRouter(prefix="/analytics",tags=["Analytics"])


def _logs(payload,db):
    q=db.query(VerificationLog)
    if payload.get("role")=="AUTHORITY" and payload.get("issuer_id") is not None:
        q=q.join(Communication,Communication.communication_id==VerificationLog.communication_id).filter(
            Communication.issuer_id==int(payload["issuer_id"]))
    return q


@router.get("/overview")
def overview(payload:dict=Depends(require_authority_or_admin),db:Session=Depends(get_db)):
    l=_logs(payload,db).all()
    counts=Counter(x.result.value for x in l)
    return {"total_verifications":len(l),"results":dict(counts),
            "documents": db.query(Communication).filter(
                Communication.issuer_id==int(payload["issuer_id"])
            ).count() if payload.get("role")=="AUTHORITY" else db.query(Communication).count()}


@router.get("/verifications")
def verification_analytics(payload:dict=Depends(require_authority_or_admin),db:Session=Depends(get_db)):
    l=_logs(payload,db).all()
    by_source=Counter(x.source.value for x in l)
    by_result=Counter(x.result.value for x in l)
    return {"by_source":dict(by_source),"by_result":dict(by_result),"total":len(l)}


@router.get("/media")
def media_analytics(payload:dict=Depends(require_authority_or_admin),db:Session=Depends(get_db)):
    q=db.query(MediaAnalysis).join(CommunicationVersion,MediaAnalysis.version_id==CommunicationVersion.id).join(
        Communication,CommunicationVersion.communication_id==Communication.id)
    if payload.get("role")=="AUTHORITY" and payload.get("issuer_id") is not None:
        q=q.filter(Communication.issuer_id==int(payload["issuer_id"]))
    rows=q.all()
    labels=Counter(x.risk_label.value for x in rows)
    return {"total_analyses":len(rows),"risk_labels":dict(labels),
            "average_risk_score":round(sum(x.risk_score or 0 for x in rows)/len(rows),6) if rows else 0}
