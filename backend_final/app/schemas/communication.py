from datetime import datetime
from pydantic import BaseModel, Field
from app.models.communication import MediaType


class CommunicationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=64)
    media_type: MediaType
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class CommunicationUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=64)
    status: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


class SignedRegistration(BaseModel):
    issuer_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=500)
    description: str | None = Field(default=None, max_length=5000)
    category: str | None = Field(default=None, max_length=64)
    media_type: MediaType
    sha256: str = Field(min_length=64, max_length=64)
    signature: str = Field(min_length=1, max_length=10000)
    signing_key_id: str = Field(min_length=1, max_length=64)
    file_name: str | None = Field(default=None, max_length=255)
    mime_type: str | None = Field(default=None, max_length=128)
    file_size_bytes: int | None = Field(default=None, ge=0)
    valid_from: datetime | None = None
    valid_until: datetime | None = None
