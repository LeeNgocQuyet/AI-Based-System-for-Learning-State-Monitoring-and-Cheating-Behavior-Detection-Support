from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import ServicePrincipal, decode_token
from app.models.user import User
from app.models.enums import AccountStatus, UserRole

bearer_scheme = HTTPBearer(auto_error=False)


def get_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User | ServicePrincipal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})

    token_type = payload.get("token_type")
    if token_type == "service":
        allowed = payload.get("allowed_sources", [])
        if not isinstance(allowed, list) or not allowed or any(not isinstance(x, str) for x in allowed):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid service token")
        return ServicePrincipal(service_name=str(payload["sub"]), allowed_sources=frozenset(allowed))

    if token_type != "user_access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
    try:
        user_id = UUID(payload["sub"])
    except (ValueError, TypeError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
    user = db.get(User, user_id)
    if user is None or user.status != AccountStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account unavailable")
    return user


def require_learner(principal: Annotated[User | ServicePrincipal, Depends(get_principal)]) -> User:
    if not isinstance(principal, User) or principal.role != UserRole.LEARNER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Learner role required")
    return principal


def require_instructor(principal: Annotated[User | ServicePrincipal, Depends(get_principal)]) -> User:
    if not isinstance(principal, User) or principal.role != UserRole.INSTRUCTOR:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Instructor role required")
    return principal
