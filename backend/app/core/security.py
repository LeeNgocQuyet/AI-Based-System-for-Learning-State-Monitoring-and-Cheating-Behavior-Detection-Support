from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, VerifyMismatchError

from app.core.config import settings
from app.models.enums import EventSource

_password_hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2, hash_len=32, salt_len=16)


@dataclass(frozen=True)
class ServicePrincipal:
    service_name: str
    allowed_sources: frozenset[str]


def hash_password(password: str) -> str:
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hasher.verify(password_hash, password)
    except (VerificationError, VerifyMismatchError):
        return False


def create_user_access_token(user_id: UUID, expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "token_type": "user_access",
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes or settings.access_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_service_token(service_name: str, allowed_sources: set[EventSource | str], expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    values = sorted(source.value if isinstance(source, EventSource) else str(source) for source in allowed_sources)
    payload = {
        "sub": service_name,
        "token_type": "service",
        "allowed_sources": values,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes or settings.service_token_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm], options={"require": ["exp", "iat", "sub", "token_type"]})
