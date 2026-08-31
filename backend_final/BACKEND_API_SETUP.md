# PramaanScan Backend API

## Run

From the project root:

```powershell
.\venv\Scripts\Activate.ps1
$env:PYTHONPATH=".\backend"
python .\backend\create_db.py
uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`

## New frontend-facing API groups

- Authentication: login, admin login, institution login, refresh, me, logout
- Dashboard statistics
- Communication/document list, filters, pagination, update, archive
- Signed-version upload/registration
- QR metadata and PNG image
- Verification logs
- Analytics
- Admin institution management
- Admin user management
- Audit logs
- Profile and password
- Settings

## Important signing design

The API never receives a private Ed25519 key. The signed-version upload endpoint receives the file, signing key ID and Ed25519 signature, computes SHA-256 itself, and verifies the signature against the registered public key before creating the immutable version.

Existing multimodal ML and cryptographic verification endpoints are preserved.

## Environment

Set `JWT_SECRET` to a long random value before deployment. You can also set:

- `DATABASE_URL`
- `PUBLIC_BASE_URL`
- `CORS_ORIGINS`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `REFRESH_TOKEN_EXPIRE_DAYS`
