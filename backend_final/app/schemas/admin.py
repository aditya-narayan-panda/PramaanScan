from pydantic import BaseModel, EmailStr, Field


class InstitutionCreate(BaseModel):
    institution_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=32)


class InstitutionUpdate(BaseModel):
    institution_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, max_length=32)
    status: str | None = None


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    role: str = Field(pattern="^(ADMIN|AUTHORITY)$")
    issuer_id: int | None = None


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    role: str | None = Field(default=None, pattern="^(ADMIN|AUTHORITY)$")
    issuer_id: int | None = None
    is_active: bool | None = None


class SettingsUpdate(BaseModel):
    language: str | None = Field(default=None, max_length=32)
    theme: str | None = Field(default=None, pattern="^(system|light|dark)$")
    notifications_enabled: bool | None = None
    email_notifications: bool | None = None
