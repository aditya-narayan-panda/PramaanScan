import enum
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer, BigInteger, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class MediaType(str, enum.Enum):
    TEXT = "TEXT"
    DOCUMENT = "DOCUMENT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"


class CommunicationStatus(str, enum.Enum):
    """Lifecycle state of the record itself. NOT the same as the six verification-result
    states (VERIFIED/MODIFIED/UNSIGNED/REVOKED/INVALID/EXPIRED) -- those are computed at
    verification time by comparing an uploaded hash against this data."""
    CURRENT = "CURRENT"
    SUPERSEDED = "SUPERSEDED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"


class Communication(Base):
    """A single official notice/message an issuer publishes. Holds no file content itself --
    each edit creates a new CommunicationVersion, preserving full provenance history."""
    __tablename__ = "communications"

    id: Mapped[int] = mapped_column(primary_key=True)
    communication_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(String(64), nullable=True)  # e.g. NOTICE, EMERGENCY, PRESS_RELEASE
    media_type: Mapped[MediaType] = mapped_column(SAEnum(MediaType, name="media_type"), nullable=False)

    status: Mapped[CommunicationStatus] = mapped_column(
        SAEnum(CommunicationStatus, name="communication_status"),
        nullable=False, default=CommunicationStatus.CURRENT,
    )
    current_version_id: Mapped[int | None] = mapped_column(
        ForeignKey("communication_versions.id", use_alter=True, name="fk_current_version"), nullable=True
    )

    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issuer: Mapped["Issuer"] = relationship(back_populates="communications")
    versions: Mapped[list["CommunicationVersion"]] = relationship(
        back_populates="communication",
        foreign_keys="CommunicationVersion.communication_id",
        order_by="CommunicationVersion.version_number",
    )
    current_version: Mapped["CommunicationVersion | None"] = relationship(
        foreign_keys=[current_version_id], post_update=True
    )


class CommunicationVersion(Base):
    """One immutable signed snapshot of a Communication. Re-signing/editing content
    creates a new row here rather than mutating an old one -- this IS the provenance trail."""
    __tablename__ = "communication_versions"
    __table_args__ = (UniqueConstraint("communication_id", "version_number", name="uq_comm_version"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    communication_id: Mapped[int] = mapped_column(ForeignKey("communications.id"), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)

    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    signature: Mapped[str] = mapped_column(Text, nullable=False)
    key_id: Mapped[int] = mapped_column(ForeignKey("signing_keys.id"), nullable=False)

    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    # Privacy-aware processing: raw uploads are hashed and (optionally) discarded rather than
    # permanently retained. storage_ref is nullable and may point at short-lived object storage.
    storage_ref: Mapped[str | None] = mapped_column(String(512), nullable=True)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    communication: Mapped["Communication"] = relationship(
        back_populates="versions", foreign_keys=[communication_id]
    )
    signing_key: Mapped["SigningKey"] = relationship(back_populates="versions")
    media_analysis: Mapped["MediaAnalysis | None"] = relationship(back_populates="version", uselist=False)
