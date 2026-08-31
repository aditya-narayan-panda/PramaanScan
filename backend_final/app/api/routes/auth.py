from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.auth import (
    LoginRequest, TokenResponse, UserResponse, RefreshRequest,
)
from app.security.auth import (
    create_access_token, create_refresh_token,
    decode_refresh_token, verify_password,
)
from app.security.permissions import get_current_user_payload
from app.services.audit import record_audit

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _login(request: LoginRequest, expected_role: UserRole | None, db: Session):
    user = db.query(User).filter(User.email == request.email).first()
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.",
                            headers={"WWW-Authenticate": "Bearer"})
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive.")
    if expected_role is not None and user.role != expected_role:
        raise HTTPException(status_code=403, detail=f"{expected_role.value} login required.")

    # CRITICAL: Check institution suspension for AUTHORITY users
    if user.role == UserRole.AUTHORITY and user.issuer_id is not None:
        from app.models.issuer import Issuer, IssuerStatus
        issuer = db.query(Issuer).filter(Issuer.id == user.issuer_id).first()
        if issuer is not None and issuer.status == IssuerStatus.SUSPENDED:
            raise HTTPException(
                status_code=403,
                detail="Your institution has been suspended. Contact the platform administrator."
            )

    user.last_login_at = datetime.now(timezone.utc)
    record_audit(db, "LOGIN", user.id, "USER", user.id, {"role": user.role.value})
    db.commit()
    return {
        "access_token": create_access_token(user.id, user.role.value, user.issuer_id),
        "refresh_token": create_refresh_token(user.id, user.role.value, user.issuer_id),
        "token_type": "bearer",
    }


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    return _login(request, None, db)


@router.post("/admin/login", response_model=TokenResponse)
def admin_login(request: LoginRequest, db: Session = Depends(get_db)):
    return _login(request, UserRole.ADMIN, db)


@router.post("/institution/login", response_model=TokenResponse)
def institution_login(request: LoginRequest, db: Session = Depends(get_db)):
    return _login(request, UserRole.AUTHORITY, db)


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    try:
        payload = decode_refresh_token(request.refresh_token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token.")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User account is unavailable.")

    # Check if institution is still active for AUTHORITY users
    if user.role == UserRole.AUTHORITY and user.issuer_id is not None:
        from app.models.issuer import Issuer, IssuerStatus
        issuer = db.query(Issuer).filter(Issuer.id == user.issuer_id).first()
        if issuer is not None and issuer.status == IssuerStatus.SUSPENDED:
            raise HTTPException(
                status_code=403,
                detail="Your institution has been suspended."
            )

    # Check server-side revocation: if jti is in revoked list, reject
    jti = payload.get("jti")
    if jti:
        try:
            from app.models.revoked_token import RevokedToken
            revoked = db.query(RevokedToken).filter(RevokedToken.jti == jti).first()
            if revoked:
                raise HTTPException(status_code=401, detail="Refresh token has been revoked.")
        except ImportError:
            pass  # RevokedToken model not yet created, skip check

    return {
        "access_token": create_access_token(user.id, user.role.value, user.issuer_id),
        "refresh_token": create_refresh_token(user.id, user.role.value, user.issuer_id),
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserResponse)
def get_me(payload: dict = Depends(get_current_user_payload), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is inactive.")
    return user


@router.post("/logout")
def logout(
    request: RefreshRequest | None = Body(default=None),
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    """
    Logout endpoint. Optionally accepts the refresh token in the body so it can
    be server-side revoked via its jti. If no refresh token is provided, logout
    still succeeds — the client must discard stored tokens.
    """
    if request and request.refresh_token:
        try:
            rt_payload = decode_refresh_token(request.refresh_token)
            jti = rt_payload.get("jti")
            if jti:
                try:
                    from app.models.revoked_token import RevokedToken
                    if not db.query(RevokedToken).filter(RevokedToken.jti == jti).first():
                        db.add(RevokedToken(jti=jti, user_id=int(payload["sub"])))
                except ImportError:
                    pass  # Model not available, skip
        except Exception:
            pass  # Invalid refresh token — still log out

    record_audit(db, "LOGOUT", int(payload["sub"]), "USER", payload["sub"])
    db.commit()
    return {"success": True, "message": "Logged out successfully."}
