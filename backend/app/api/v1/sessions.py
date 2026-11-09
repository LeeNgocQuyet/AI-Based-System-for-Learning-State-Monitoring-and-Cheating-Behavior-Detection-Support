from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_principal, require_learner
from app.db.session import get_db
from app.models import LearningSession, User
from app.models.enums import SessionStatus, SessionType
from app.schemas.session import (
    SessionCreate, SessionListOut, SessionOut, SessionReportResponse, SessionResponse,
    SessionStatusUpdate,
)
from app.core.security import ServicePrincipal
from app.services.event_service import build_session_report
from app.services.session_service import (
    as_utc, create_session, get_accessible_session, list_learner_sessions,
    session_duration_ms, update_session_status,
)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def to_session_out(entity: LearningSession) -> SessionOut:
    return SessionOut(
        session_id=entity.session_id,
        session_type=entity.session_type.value,
        status=entity.status.value,
        started_at=as_utc(entity.started_at),
        ended_at=as_utc(entity.ended_at),
        duration_ms=session_duration_ms(entity),
    )


def _validate_time_range(from_dt: datetime | None, to_dt: datetime | None) -> None:
    if from_dt and to_dt and from_dt >= to_dt:
        raise HTTPException(status_code=422, detail="from must be earlier than to")


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED, summary="Create and start a session")
def create_learning_session(
    payload: SessionCreate,
    learner: Annotated[User, Depends(require_learner)],
    db: Annotated[Session, Depends(get_db)],
):
    entity = create_session(db, learner, SessionType(payload.session_type.value))
    return {"data": to_session_out(entity)}


@router.get("/mine", response_model=SessionListOut, summary="List sessions owned by current learner")
def get_my_sessions(
    learner: Annotated[User, Depends(require_learner)],
    db: Annotated[Session, Depends(get_db)],
    session_type: SessionType | None = None,
    status_filter: SessionStatus | None = Query(default=None, alias="status"),
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    _validate_time_range(from_dt, to_dt)
    items, total = list_learner_sessions(db, learner, session_type, status_filter, from_dt, to_dt, page, page_size)
    return {"data": [to_session_out(item) for item in items], "page": page, "page_size": page_size, "total": total}


@router.get("/{session_id}", response_model=SessionResponse, summary="Get a session within caller's access scope")
def get_session(
    session_id: UUID,
    principal: Annotated[User | ServicePrincipal, Depends(get_principal)],
    db: Annotated[Session, Depends(get_db)],
):
    entity = get_accessible_session(db, session_id, principal)
    return {"data": to_session_out(entity)}


@router.patch("/{session_id}/status", response_model=SessionResponse, summary="Pause, resume, or end a session")
def patch_session_status(
    session_id: UUID,
    payload: SessionStatusUpdate,
    learner: Annotated[User, Depends(require_learner)],
    db: Annotated[Session, Depends(get_db)],
):
    entity = db.get(LearningSession, session_id)
    if entity is None or entity.learner_id != learner.user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    updated = update_session_status(db, entity, SessionStatus(payload.status.value))
    return {"data": to_session_out(updated)}


@router.post("/{session_id}/start", response_model=SessionResponse, summary="Resume a paused session")
def start_session(
    session_id: UUID,
    learner: Annotated[User, Depends(require_learner)],
    db: Annotated[Session, Depends(get_db)],
):
    entity = db.get(LearningSession, session_id)
    if entity is None or entity.learner_id != learner.user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    updated = update_session_status(db, entity, SessionStatus.ACTIVE)
    return {"data": to_session_out(updated)}


@router.post("/{session_id}/end", response_model=SessionResponse, summary="End a session")
def end_session(
    session_id: UUID,
    learner: Annotated[User, Depends(require_learner)],
    db: Annotated[Session, Depends(get_db)],
):
    entity = db.get(LearningSession, session_id)
    if entity is None or entity.learner_id != learner.user_id:
        raise HTTPException(status_code=404, detail="Session not found")
    updated = update_session_status(db, entity, SessionStatus.ENDED)
    return {"data": to_session_out(updated)}


@router.get("/{session_id}/report", response_model=SessionReportResponse, summary="Get session event summary")
def get_session_report(
    session_id: UUID,
    principal: Annotated[User | ServicePrincipal, Depends(get_principal)],
    db: Annotated[Session, Depends(get_db)],
):
    entity = get_accessible_session(db, session_id, principal)
    return {"data": build_session_report(db, entity)}
