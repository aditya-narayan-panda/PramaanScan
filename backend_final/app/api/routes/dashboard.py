from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.communication import Communication, CommunicationStatus, CommunicationVersion
from app.models.issuer import Issuer
from app.models.media_analysis import MediaAnalysis, RiskLabel
from app.models.user import User
from app.models.verification_log import VerificationLog
from app.security.permissions import require_authority_or_admin

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/stats")
def dashboard_stats(payload: dict = Depends(require_authority_or_admin), db: Session = Depends(get_db)):
    issuer_id = payload.get("issuer_id")
    comm_q = db.query(Communication)
    user_q = db.query(User)
    if payload.get("role") == "AUTHORITY" and issuer_id is not None:
        comm_q = comm_q.filter(Communication.issuer_id == int(issuer_id))
        user_q = user_q.filter(User.issuer_id == int(issuer_id))

    total_documents = comm_q.count()
    revoked_documents = comm_q.filter(Communication.status == CommunicationStatus.REVOKED).count()
    verifications = db.query(VerificationLog)
    if payload.get("role") == "AUTHORITY" and issuer_id is not None:
        # verification logs use communication_id rather than issuer FK
        verifications = verifications.join(
            Communication, Communication.communication_id == VerificationLog.communication_id
        ).filter(Communication.issuer_id == int(issuer_id))
    verified = verifications.filter(VerificationLog.result == "VERIFIED").count()
    unsigned = verifications.filter(VerificationLog.result == "UNSIGNED").count()
    high_risk = db.query(MediaAnalysis).join(CommunicationVersion, MediaAnalysis.version_id == CommunicationVersion.id).join(Communication, CommunicationVersion.communication_id == Communication.id)
    if payload.get("role") == "AUTHORITY" and issuer_id is not None:
        high_risk = high_risk.filter(Communication.issuer_id == int(issuer_id))
    high_risk_count = high_risk.filter(MediaAnalysis.risk_label == RiskLabel.HIGH).count()
    return {
        "total_documents": total_documents,
        "revoked_documents": revoked_documents,
        "total_verifications": verifications.count(),
        "verified_verifications": verified,
        "unsigned_verifications": unsigned,
        "high_risk_media": high_risk_count,
        "users": user_q.count() if payload.get("role") == "AUTHORITY" else db.query(User).count(),
        "institutions": db.query(Issuer).count() if payload.get("role") == "ADMIN" else 1,
    }
