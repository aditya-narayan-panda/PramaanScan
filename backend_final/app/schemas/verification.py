from pydantic import BaseModel


class VerificationResponse(BaseModel):
    status: str
    reason: str | None = None
    sha256: str
    filename: str | None = None
