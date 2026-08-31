import enum
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class VerificationResult(str, enum.Enum):
    VERIFIED = "VERIFIED"
    MODIFIED = "MODIFIED"
    UNSIGNED = "UNSIGNED"
    REVOKED = "REVOKED"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"


class VerificationSource(str, enum.Enum):
    QR = "QR"
    COMMUNICATION_ID = "COMMUNICATION_ID"
    FILE_UPLOAD = "FILE_UPLOAD"


class VerificationLog(Base):
    """Append-only audit trail of every public verification attempt, including ones for
    unregistered/tampered content. Deliberately has NO foreign key to Communication so a
    verification attempt is still logged even when nothing matches. IP is hashed, never stored
    raw, per privacy-aware processing."""
    __tablename__ = "verification_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    communication_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    result: Mapped[VerificationResult] = mapped_column(
        SAEnum(VerificationResult, name="verification_result"), nullable=False
    )
    source: Mapped[VerificationSource] = mapped_column(
        SAEnum(VerificationSource, name="verification_source"), nullable=False
    )
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
