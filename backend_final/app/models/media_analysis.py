import enum
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, Float, Boolean, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class RiskLabel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    INCONCLUSIVE = "INCONCLUSIVE"


class MediaAnalysis(Base):
    """Secondary, probabilistic manipulation-risk signal for audio/video/image versions.
    Explicitly advisory: is_advisory is always True and this table is never consulted by the
    cryptographic verification path (services/verification.py). It is surfaced to the user
    alongside -- never instead of -- the signature/hash result."""
    __tablename__ = "media_analyses"

    id: Mapped[int] = mapped_column(primary_key=True)
    version_id: Mapped[int] = mapped_column(
        ForeignKey("communication_versions.id"), unique=True, nullable=False
    )
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0.0-1.0
    risk_label: Mapped[RiskLabel] = mapped_column(
        SAEnum(RiskLabel, name="risk_label"), nullable=False, default=RiskLabel.INCONCLUSIVE
    )
    model_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON-encoded findings
    is_advisory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    version: Mapped["CommunicationVersion"] = relationship(back_populates="media_analysis")
