from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import base  # noqa: F401
from app.core.config import settings
from app.api.routes import (
    health, verification, communications, auth, revocation, media,
    dashboard, admin, audit, logs, analytics, profile, qr, documents, language,
)

app = FastAPI(title="PramaanScan API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    # Local Vite development may move between ports (5173, 5178, 5179, ...).
    # Keep this regex development-only so the public production CORS policy
    # remains explicit and controlled by CORS_ORIGINS.
    allow_origin_regex=(r"^https?://(localhost|127\.0\.0\.1):\d+$" if settings.APP_ENV.lower() == "development" else None),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in [
    health.router, qr.router, verification.router, communications.router, auth.router,
    revocation.router, media.router, dashboard.router, admin.router,
    audit.router, logs.router, analytics.router, profile.router,
    profile.settings_router, documents.router, language.router,
]:
    app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {"project": "PramaanScan", "status": "backend running", "api_version": "v1"}
