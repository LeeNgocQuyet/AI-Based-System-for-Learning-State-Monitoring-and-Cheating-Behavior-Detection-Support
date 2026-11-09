from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import ServicePrincipal
from app.models import InstructorSessionAccess, LearningSession, User
from app.models.enums import SessionStatus, SessionType, UserRole


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def session_duration_ms(entity: LearningSession) -> int:
    duration = int(entity.accumulated_active_ms or 0)
    if entity.status == SessionStatus.ACTIVE and entity.active_started_at is not None:
        start = as_utc(entity.active_started_at)
        now = utc_now()
        duration += max(0, int((now - start).total_seconds() * 1000))
    return duration


def create_session(db: Session, learner: User, session_type: SessionType) -> LearningSession:
    now = utc_now()
    entity = LearningSession(
        learner_id=learner.user_id,
        session_type=session_type,
        status=SessionStatus.ACTIVE,
        started_at=now,
        active_started_at=now,
        paused_at=None,
        ended_at=None,
        accumulated_active_ms=0,
    )
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def get_accessible_session(db: Session, session_id: UUID, principal: User | ServicePrincipal) -> LearningSession:
    entity = db.get(LearningSession, session_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if isinstance(principal, ServicePrincipal):
        raise HTTPException(status_code=403, detail="Service tokens cannot query sessions")

    if principal.role == UserRole.LEARNER and entity.learner_id == principal.user_id:
        return entity

    if principal.role == UserRole.INSTRUCTOR:
        grant = db.get(InstructorSessionAccess, (principal.user_id, session_id))
        if grant is not None:
            return entity

    # Hide existence of sessions outside the caller's scope.
    raise HTTPException(status_code=404, detail="Session not found")


def update_session_status(db: Session, entity: LearningSession, target: SessionStatus) -> LearningSession:
    now = utc_now()
    if entity.status == SessionStatus.ENDED:
        raise HTTPException(status_code=409, detail="Ended session is terminal")
    if entity.status == target:
        raise HTTPException(status_code=409, detail=f"Session is already {target.value}")
    if target == SessionStatus.PAUSED and entity.session_type == SessionType.EXAM:
        raise HTTPException(status_code=400, detail="EXAM sessions cannot be paused")

    if entity.status == SessionStatus.ACTIVE and target == SessionStatus.PAUSED:
        active_start = as_utc(entity.active_started_at)
        entity.accumulated_active_ms += max(0, int((now - active_start).total_seconds() * 1000)) if active_start else 0
        entity.active_started_at = None
        entity.paused_at = now
        entity.status = SessionStatus.PAUSED
    elif entity.status == SessionStatus.PAUSED and target == SessionStatus.ACTIVE:
        entity.paused_at = None
        entity.active_started_at = now
        entity.status = SessionStatus.ACTIVE
    elif target == SessionStatus.ENDED and entity.status in {SessionStatus.ACTIVE, SessionStatus.PAUSED}:
        if entity.status == SessionStatus.ACTIVE and entity.active_started_at is not None:
            active_start = as_utc(entity.active_started_at)
            entity.accumulated_active_ms += max(0, int((now - active_start).total_seconds() * 1000))
        entity.active_started_at = None
        entity.paused_at = None
        entity.ended_at = now
        entity.status = SessionStatus.ENDED
    else:
        raise HTTPException(status_code=400, detail="Unsupported session state transition")

    entity.updated_at = now
    db.add(entity)
    db.commit()
    db.refresh(entity)
    return entity


def list_learner_sessions(
    db: Session,
    learner: User,
    session_type: SessionType | None,
    status_filter: SessionStatus | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
    page: int,
    page_size: int,
):
    query = select(LearningSession).where(LearningSession.learner_id == learner.user_id)
    if session_type:
        query = query.where(LearningSession.session_type == session_type)
    if status_filter:
        query = query.where(LearningSession.status == status_filter)
    if from_dt:
        query = query.where(LearningSession.started_at >= from_dt)
    if to_dt:
        query = query.where(LearningSession.started_at < to_dt)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(LearningSession.started_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


def list_instructor_sessions(
    db: Session,
    instructor: User,
    session_type: SessionType | None,
    status_filter: SessionStatus | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
    page: int,
    page_size: int,
):
    query = (
        select(LearningSession, User)
        .join(InstructorSessionAccess, InstructorSessionAccess.session_id == LearningSession.session_id)
        .join(User, User.user_id == LearningSession.learner_id)
        .where(InstructorSessionAccess.instructor_id == instructor.user_id)
    )
    if session_type:
        query = query.where(LearningSession.session_type == session_type)
    if status_filter:
        query = query.where(LearningSession.status == status_filter)
    if from_dt:
        query = query.where(LearningSession.started_at >= from_dt)
    if to_dt:
        query = query.where(LearningSession.started_at < to_dt)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.order_by(LearningSession.started_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return rows, total
