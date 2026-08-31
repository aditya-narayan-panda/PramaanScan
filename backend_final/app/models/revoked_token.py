"""
Server-side refresh token revocation store.

When a user logs out and provides their refresh token, the token's jti (JWT ID)
is stored here so subsequent attempts to use it are rejected immediately.

In production, old entries should be cleaned up after REFRESH_TOKEN_EXPIRE_DAYS.
"""
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base_class import Base


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
