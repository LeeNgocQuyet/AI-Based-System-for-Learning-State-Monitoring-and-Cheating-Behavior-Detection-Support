from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings, validate_settings

validate_settings()

app = FastAPI(
    title=settings.app_name,
    version="1.2.0",
    description=(
        "Session/Event API for Group 3. Session creation starts monitoring immediately. "
        "Learner ownership, instructor grants, and AI service source permissions are enforced on the server."
    ),
    openapi_url=f"{settings.api_prefix}/openapi.json",
    docs_url=f"{settings.api_prefix}/docs",
    redoc_url=f"{settings.api_prefix}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "ok", "service": "session-event-api", "version": "1.2.0"}
