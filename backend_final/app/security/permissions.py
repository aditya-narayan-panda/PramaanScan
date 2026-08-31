from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.security.auth import decode_access_token


ROLES = {"PUBLIC", "AUTHORITY", "ADMIN"}

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict:
    """
    Extract and validate the JWT access token.
    """

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if payload.get("institution_suspended") is True:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Institution is suspended.",
        )

    user_id = payload.get("sub")
    role = payload.get("role")

    if not user_id or role not in ROLES:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload


def require_admin(
    payload: dict = Depends(get_current_user_payload),
) -> dict:
    """
    Allow only ADMIN users.
    """

    if payload.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )

    return payload


def require_authority_or_admin(
    payload: dict = Depends(get_current_user_payload),
) -> dict:
    """
    Allow ADMIN and AUTHORITY users.
    """

    if payload.get("role") not in {"ADMIN", "AUTHORITY"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Authority or administrator access required.",
        )

    return payload


def require_role(required_role: str):
    """
    Generic role dependency.
    """

    if required_role not in ROLES:
        raise ValueError(
            f"Unsupported role: {required_role}"
        )

    def dependency(
        payload: dict = Depends(get_current_user_payload),
    ) -> dict:

        if payload.get("role") != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"{required_role} access required.",
            )

        return payload

    return dependency
