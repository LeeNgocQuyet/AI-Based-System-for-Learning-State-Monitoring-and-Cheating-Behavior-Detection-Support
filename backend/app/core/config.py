from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

DEFAULT_DEV_JWT_SECRET = "group3-secure-dev-jwt-secret-key-32chars-min-local-demo"


def _resolve_jwt_secret() -> str:
    raw = os.getenv("JWT_SECRET", "").strip()
    if not raw or raw.lower().startswith("replace-this"):
        return DEFAULT_DEV_JWT_SECRET
    return raw


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Group 3 Learning Monitoring API")
    environment: str = os.getenv("ENVIRONMENT", "development")
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./learning_monitor.db")
    jwt_secret: str = _resolve_jwt_secret()
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
    service_token_minutes: int = int(os.getenv("SERVICE_TOKEN_MINUTES", "60"))
    enable_phone_detection: bool = os.getenv("ENABLE_PHONE_DETECTION", "false").lower() == "true"
    cors_origins: tuple[str, ...] = tuple(
        origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",") if origin.strip()
    )


settings = Settings()


def validate_settings() -> None:
    is_prod = settings.environment.lower() in {"production", "prod"}
    if is_prod:
        raw_secret = os.getenv("JWT_SECRET", "").strip()
        if len(raw_secret) < 32 or raw_secret.lower().startswith("replace-this"):
            raise RuntimeError("In production, JWT_SECRET must be set to a private random value of at least 32 characters")
