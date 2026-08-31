from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.issuer import Issuer, IssuerStatus
from app.models.user import User, UserRole
from app.schemas.admin import InstitutionCreate, InstitutionUpdate, UserCreate, UserUpdate
from app.security.auth import hash_password
from app.security.permissions import require_admin
from app.services.audit import record_audit

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/institutions")
def list_institutions(page: int = 1, page_size: int = 20, search: str | None = None,
                      status: str | None = None, payload: dict = Depends(require_admin),
                      db: Session = Depends(get_db)):
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    q = db.query(Issuer)
    if search: q = q.filter(Issuer.institution_name.ilike(f"%{search.strip()}%"))
    if status: q = q.filter(Issuer.status == status.upper())
    total = q.count()
    items = q.order_by(Issuer.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"items": [{"id": x.id, "institution_name": x.institution_name, "email": x.email,
                       "contact_phone": x.contact_phone, "status": x.status.value, "created_at": x.created_at}
             for x in items], "page": page, "page_size": page_size, "total": total,
            "pages": (total + page_size - 1)//page_size}


@router.post("/institutions")
def create_institution(request: InstitutionCreate, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(Issuer).filter(Issuer.email == request.email).first():
        raise HTTPException(status_code=409, detail="Institution email already exists.")
    x = Issuer(**request.model_dump())
    db.add(x); db.flush()
    record_audit(db, "CREATE_INSTITUTION", int(payload["sub"]), "ISSUER", x.id)
    db.commit(); db.refresh(x)
    return {"success": True, "institution": {"id": x.id, "institution_name": x.institution_name,
            "email": x.email, "contact_phone": x.contact_phone, "status": x.status.value}}


@router.get("/institutions/{institution_id}")
def get_institution(institution_id: int, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    x = db.query(Issuer).filter(Issuer.id == institution_id).first()
    if not x: raise HTTPException(status_code=404, detail="Institution not found.")
    return {"id": x.id, "institution_name": x.institution_name, "email": x.email,
            "contact_phone": x.contact_phone, "status": x.status.value, "created_at": x.created_at,
            "users": [{"id": u.id, "email": u.email, "full_name": u.full_name, "role": u.role.value, "is_active": u.is_active} for u in x.users]}


@router.put("/institutions/{institution_id}")
def update_institution(institution_id: int, request: InstitutionUpdate, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    x = db.query(Issuer).filter(Issuer.id == institution_id).first()
    if not x: raise HTTPException(status_code=404, detail="Institution not found.")
    data = request.model_dump(exclude_unset=True)
    if "status" in data:
        try: data["status"] = IssuerStatus(data["status"].upper())
        except ValueError: raise HTTPException(status_code=400, detail="Invalid institution status.")
    for k,v in data.items(): setattr(x,k,v)
    record_audit(db, "UPDATE_INSTITUTION", int(payload["sub"]), "ISSUER", x.id)
    db.commit(); db.refresh(x)
    return {"success": True, "id": x.id, "status": x.status.value}


@router.delete("/institutions/{institution_id}")
def delete_institution(institution_id: int, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    x = db.query(Issuer).filter(Issuer.id == institution_id).first()
    if not x: raise HTTPException(status_code=404, detail="Institution not found.")
    x.status = IssuerStatus.SUSPENDED
    record_audit(db, "SUSPEND_INSTITUTION", int(payload["sub"]), "ISSUER", x.id)
    db.commit()
    return {"success": True, "message": "Institution suspended.", "id": x.id}


@router.get("/users")
def list_users(page: int = 1, page_size: int = 20, search: str | None = None, role: str | None = None,
               issuer_id: int | None = None, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    page, page_size = max(page, 1), min(max(page_size, 1), 100)
    q = db.query(User)
    if search:
        term=f"%{search.strip()}%"; q=q.filter((User.email.ilike(term)) | (User.full_name.ilike(term)))
    if role: q=q.filter(User.role == role.upper())
    if issuer_id: q=q.filter(User.issuer_id == issuer_id)
    total=q.count(); items=q.order_by(User.created_at.desc()).offset((page-1)*page_size).limit(page_size).all()
    return {"items": [{"id":u.id,"email":u.email,"full_name":u.full_name,"role":u.role.value,
                       "issuer_id":u.issuer_id,"is_active":u.is_active,"created_at":u.created_at,"last_login_at":u.last_login_at} for u in items],
            "page":page,"page_size":page_size,"total":total,"pages":(total+page_size-1)//page_size}


@router.post("/users")
def create_user(request: UserCreate, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == request.email).first():
        raise HTTPException(status_code=409, detail="User email already exists.")
    role=UserRole(request.role)
    if role == UserRole.AUTHORITY:
        if request.issuer_id is None: raise HTTPException(status_code=400, detail="AUTHORITY user requires issuer_id.")
        if not db.query(Issuer).filter(Issuer.id == request.issuer_id).first():
            raise HTTPException(status_code=404, detail="Issuer not found.")
    else:
        if request.issuer_id is not None: raise HTTPException(status_code=400, detail="ADMIN user must not have issuer_id.")
    u=User(email=request.email, password_hash=hash_password(request.password), full_name=request.full_name,
           role=role, issuer_id=request.issuer_id)
    db.add(u); db.flush()
    record_audit(db,"CREATE_USER",int(payload["sub"]),"USER",u.id,{"role":role.value})
    db.commit(); db.refresh(u)
    return {"success":True,"user":{"id":u.id,"email":u.email,"full_name":u.full_name,"role":u.role.value,"issuer_id":u.issuer_id,"is_active":u.is_active}}


@router.get("/users/{user_id}")
def get_user(user_id: int, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    u=db.query(User).filter(User.id==user_id).first()
    if not u: raise HTTPException(status_code=404, detail="User not found.")
    return {"id":u.id,"email":u.email,"full_name":u.full_name,"role":u.role.value,"issuer_id":u.issuer_id,
            "is_active":u.is_active,"created_at":u.created_at,"last_login_at":u.last_login_at}


@router.put("/users/{user_id}")
def update_user(user_id: int, request: UserUpdate, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    u=db.query(User).filter(User.id==user_id).first()
    if not u: raise HTTPException(status_code=404, detail="User not found.")
    data=request.model_dump(exclude_unset=True)
    if "role" in data: data["role"]=UserRole(data["role"])
    if "password" in data: data["password_hash"]=hash_password(data.pop("password"))
    for k,v in data.items(): setattr(u,k,v)
    if u.role == UserRole.AUTHORITY and u.issuer_id is None: raise HTTPException(status_code=400, detail="AUTHORITY user requires issuer_id.")
    if u.role == UserRole.ADMIN: u.issuer_id=None
    record_audit(db,"UPDATE_USER",int(payload["sub"]),"USER",u.id)
    db.commit(); db.refresh(u)
    return {"success":True,"id":u.id,"role":u.role.value,"issuer_id":u.issuer_id,"is_active":u.is_active}


@router.delete("/users/{user_id}")
def delete_user(user_id: int, payload: dict = Depends(require_admin), db: Session = Depends(get_db)):
    u=db.query(User).filter(User.id==user_id).first()
    if not u: raise HTTPException(status_code=404, detail="User not found.")
    if u.id==int(payload["sub"]): raise HTTPException(status_code=400, detail="You cannot deactivate yourself.")
    u.is_active=False
    record_audit(db,"DEACTIVATE_USER",int(payload["sub"]),"USER",u.id)
    db.commit()
    return {"success":True,"message":"User deactivated.","id":u.id}
