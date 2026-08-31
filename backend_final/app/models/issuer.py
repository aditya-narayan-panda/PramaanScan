import enum
from datetime import datetime

from sqlalchemy import String, DateTime, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class IssuerStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class Issuer(Base):
    """A registered institution/authority allowed to sign official communications."""
    __tablename__ = "issuers"

    id: Mapped[int] = mapped_column(primary_key=True)
    institution_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    contact_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[IssuerStatus] = mapped_column(
        SAEnum(IssuerStatus, name="issuer_status"), nullable=False, default=IssuerStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="issuer")
    signing_keys: Mapped[list["SigningKey"]] = relationship(back_populates="issuer")
    communications: Mapped[list["Communication"]] = relationship(back_populates="issuer")
