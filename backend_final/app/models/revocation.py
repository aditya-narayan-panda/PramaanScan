import enum
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class RevocationTargetType(str, enum.Enum):
    SIGNING_KEY = "SIGNING_KEY"
    COMMUNICATION = "COMMUNICATION"


class Revocation(Base):
    """Immutable record of why/when a key or communication was revoked. Kept separate from
    SigningKey.status / Communication.status so there is always a durable reason + actor trail,
    even though those tables also carry a denormalized status for fast lookups."""
    __tablename__ = "revocations"

    id: Mapped[int] = mapped_column(primary_key=True)
    target_type: Mapped[RevocationTargetType] = mapped_column(
        SAEnum(RevocationTargetType, name="revocation_target_type"), nullable=False
    )
    target_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # key_id or communication_id
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    revoked_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    revoked_by_user: Mapped["User | None"] = relationship(back_populates="revocations_made")
