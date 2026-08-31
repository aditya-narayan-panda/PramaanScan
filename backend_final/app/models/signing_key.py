import enum
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class KeyStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"


class SigningKey(Base):
    """An Ed25519 keypair belonging to one issuer.
    Prototype note: private_key_encrypted is stored app-side (encrypted at rest) for demo
    purposes only. Real deployment should move key custody to an HSM/KMS (see FUTURE_FEATURES)."""
    __tablename__ = "signing_keys"

    id: Mapped[int] = mapped_column(primary_key=True)
    key_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id"), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(32), nullable=False, default="Ed25519")
    public_key: Mapped[str] = mapped_column(Text, nullable=False)
    private_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[KeyStatus] = mapped_column(
        SAEnum(KeyStatus, name="key_status"), nullable=False, default=KeyStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    revoked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    issuer: Mapped["Issuer"] = relationship(back_populates="signing_keys")
    versions: Mapped[list["CommunicationVersion"]] = relationship(back_populates="signing_key")
