import enum
from datetime import datetime

from sqlalchemy import String, Boolean, DateTime, ForeignKey, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"          # manages authorities, keys, communications, global audit
    AUTHORITY = "AUTHORITY"  # manages only its own issuer's communications/keys


class User(Base):
    """Login identity for the private Authority and Admin dashboards.
    Public verification never requires a User row."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole, name="user_role"), nullable=False)

    # AUTHORITY users belong to exactly one issuer; ADMIN users leave this null.
    issuer_id: Mapped[int | None] = mapped_column(ForeignKey("issuers.id"), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    issuer: Mapped["Issuer | None"] = relationship(back_populates="users")
    revocations_made: Mapped[list["Revocation"]] = relationship(back_populates="revoked_by_user")
