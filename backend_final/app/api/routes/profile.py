from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.user_settings import UserSettings
from app.schemas.auth import UpdateProfileRequest, ChangePasswordRequest
from app.schemas.admin import SettingsUpdate
from app.security.auth import hash_password, verify_password
from app.security.permissions import get_current_user_payload

router=APIRouter(prefix="/profile",tags=["Profile"])
settings_router=APIRouter(prefix="/settings",tags=["Settings"])


@router.get("")
def profile(payload:dict=Depends(get_current_user_payload),db:Session=Depends(get_db)):
    u=db.query(User).filter(User.id==int(payload["sub"])).first()
    if not u: raise HTTPException(status_code=404,detail="User not found.")
    return {"id":u.id,"email":u.email,"full_name":u.full_name,"role":u.role.value,"issuer_id":u.issuer_id,
            "is_active":u.is_active,"created_at":u.created_at,"last_login_at":u.last_login_at}


@router.put("")
def update_profile(request:UpdateProfileRequest,payload:dict=Depends(get_current_user_payload),db:Session=Depends(get_db)):
    u=db.query(User).filter(User.id==int(payload["sub"])).first()
    if not u: raise HTTPException(status_code=404,detail="User not found.")
    u.full_name=request.full_name; db.commit()
    return {"success":True,"full_name":u.full_name}


@router.post("/password")
def change_password(request:ChangePasswordRequest,payload:dict=Depends(get_current_user_payload),db:Session=Depends(get_db)):
    u=db.query(User).filter(User.id==int(payload["sub"])).first()
    if not u: raise HTTPException(status_code=404,detail="User not found.")
    if not verify_password(request.current_password,u.password_hash):
        raise HTTPException(status_code=400,detail="Current password is incorrect.")
    u.password_hash=hash_password(request.new_password); db.commit()
    return {"success":True,"message":"Password changed successfully."}


@settings_router.get("")
def get_settings(payload:dict=Depends(get_current_user_payload),db:Session=Depends(get_db)):
    s=db.query(UserSettings).filter(UserSettings.user_id==int(payload["sub"])).first()
    if s is None:
        s=UserSettings(user_id=int(payload["sub"])); db.add(s); db.commit(); db.refresh(s)
    return {"language":s.language,"theme":s.theme,"notifications_enabled":s.notifications_enabled,
            "email_notifications":s.email_notifications}


@settings_router.put("")
def update_settings(request:SettingsUpdate,payload:dict=Depends(get_current_user_payload),db:Session=Depends(get_db)):
    s=db.query(UserSettings).filter(UserSettings.user_id==int(payload["sub"])).first()
    if s is None: s=UserSettings(user_id=int(payload["sub"])); db.add(s)
    for k,v in request.model_dump(exclude_unset=True).items(): setattr(s,k,v)
    db.commit(); db.refresh(s)
    return {"success":True,"language":s.language,"theme":s.theme,
            "notifications_enabled":s.notifications_enabled,"email_notifications":s.email_notifications}
