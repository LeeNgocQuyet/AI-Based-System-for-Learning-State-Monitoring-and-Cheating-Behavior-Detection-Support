from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import ServicePrincipal
from app.core.config import settings
from app.models import Event, LearningSession, User
from app.models.enums import EventSource, EventType, SessionStatus, Severity, UserRole
from app.schemas.event import EventIngest
from app.services.session_service import as_utc, get_accessible_session


EVENT_MESSAGES: dict[EventType, str] = {
    EventType.EYES_CLOSED_LONG: "Hệ thống ghi nhận dấu hiệu nhắm mắt kéo dài.",
    EventType.YAWN_DETECTED: "Hệ thống ghi nhận dấu hiệu ngáp.",
    EventType.HEAD_NOD_DETECTED: "Hệ thống ghi nhận dấu hiệu gật đầu.",
    EventType.LOOK_AWAY_DETECTED: "Hệ thống ghi nhận dấu hiệu nhìn lệch khỏi màn hình.",
    EventType.FACE_NOT_DETECTED: "Hệ thống tạm thời không phát hiện khuôn mặt trong khung hình.",
    EventType.MULTIPLE_FACES_DETECTED: "Hệ thống phát hiện nhiều hơn một khuôn mặt trong khung hình.",
    EventType.PHONE_DETECTED: "Hệ thống ghi nhận một vật thể có thể là điện thoại.",
    EventType.TAB_HIDDEN: "Trình duyệt ghi nhận tab học/thi không còn hiển thị.",
    EventType.CAMERA_LOST: "Kết nối camera bị gián đoạn.",
    EventType.CONNECTION_LOST: "Kết nối với một thành phần hệ thống bị gián đoạn.",
}


def normalize_severity(event_type: EventType, duration_ms: int | None) -> Severity:
    duration = duration_ms or 0
    if event_type == EventType.EYES_CLOSED_LONG:
        return Severity.HIGH if duration >= 5000 else Severity.MEDIUM if duration >= 2500 else Severity.LOW
    if event_type == EventType.YAWN_DETECTED:
        return Severity.LOW
    if event_type == EventType.HEAD_NOD_DETECTED:
        return Severity.MEDIUM if duration >= 1500 else Severity.LOW
    if event_type == EventType.LOOK_AWAY_DETECTED:
        return Severity.MEDIUM if duration >= 3000 else Severity.LOW
    if event_type == EventType.FACE_NOT_DETECTED:
        return Severity.HIGH if duration >= 5000 else Severity.MEDIUM
    if event_type in {EventType.MULTIPLE_FACES_DETECTED, EventType.PHONE_DETECTED, EventType.CAMERA_LOST, EventType.CONNECTION_LOST}:
        return Severity.HIGH
    if event_type == EventType.TAB_HIDDEN:
        return Severity.MEDIUM
    return Severity.INFO


def _same_payload(existing: Event, payload: EventIngest) -> bool:
    return (
        existing.session_id == payload.session_id
        and existing.schema_version == payload.schema_version
        and existing.event_type.value == payload.event_type.value
        and as_utc(existing.occurred_at) == payload.occurred_at.astimezone(timezone.utc)
        and existing.source.value == payload.source.value
        and existing.duration_ms == payload.duration_ms
        and (float(existing.confidence) if existing.confidence is not None else None) == payload.confidence
        and (existing.metadata_json or {}) == payload.metadata
    )


def ingest_event(db: Session, session_id: UUID, payload: EventIngest, principal: User | ServicePrincipal) -> tuple[Event, bool]:
    if payload.session_id != session_id:
        raise HTTPException(status_code=400, detail="session_id in body must match path parameter")
    if payload.event_type == EventType.PHONE_DETECTED and not settings.enable_phone_detection:
        raise HTTPException(status_code=403, detail="PHONE_DETECTED is experimental and disabled by configuration")

    # Authorize the caller against the target session before looking up event_id.
    # This prevents a caller who guesses/reuses an event UUID from reading an
    # existing event through the idempotency response.
    session = db.get(LearningSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    if isinstance(principal, ServicePrincipal):
        if payload.source.value not in principal.allowed_sources:
            raise HTTPException(status_code=403, detail="Service token is not permitted to emit this source")
        if payload.source == EventSource.BROWSER:
            raise HTTPException(status_code=403, detail="Service tokens cannot emit browser events")
    else:
        if payload.source != EventSource.BROWSER:
            raise HTTPException(status_code=403, detail="User tokens may only emit BROWSER events")
        if principal.role != UserRole.LEARNER or session.learner_id != principal.user_id:
            raise HTTPException(status_code=404, detail="Session not found")

    if payload.source == EventSource.AI_LEARNING and session.session_type.value != "LEARNING":
        raise HTTPException(status_code=403, detail="AI_LEARNING events require a LEARNING session")
    if payload.source == EventSource.AI_EXAM and session.session_type.value != "EXAM":
        raise HTTPException(status_code=403, detail="AI_EXAM events require an EXAM session")

    existing = db.get(Event, payload.event_id)
    if existing is not None:
        if existing.session_id != session_id:
            raise HTTPException(status_code=409, detail="event_id already belongs to another session")
        if _same_payload(existing, payload):
            return existing, True
        raise HTTPException(status_code=409, detail="event_id already exists with a different payload")

    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(status_code=409, detail="Events can only be ingested while session is ACTIVE")

    occurred_at = payload.occurred_at.astimezone(timezone.utc)
    started_at = as_utc(session.started_at)
    if occurred_at < started_at:
        raise HTTPException(status_code=422, detail="occurred_at cannot be earlier than session.started_at")
    now = datetime.now(timezone.utc)
    if occurred_at > now.replace(microsecond=0) and (occurred_at - now).total_seconds() > 300:
        raise HTTPException(status_code=422, detail="occurred_at cannot be more than 5 minutes in the future")

    entity = Event(
        event_id=payload.event_id,
        session_id=session_id,
        schema_version=payload.schema_version,
        event_type=EventType(payload.event_type.value),
        occurred_at=occurred_at,
        received_at=now,
        source=EventSource(payload.source.value),
        severity=normalize_severity(EventType(payload.event_type.value), payload.duration_ms),
        duration_ms=payload.duration_ms,
        confidence=Decimal(str(payload.confidence)) if payload.confidence is not None else None,
        message=EVENT_MESSAGES[EventType(payload.event_type.value)],
        metadata_json=payload.metadata,
    )
    db.add(entity)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Resolve a concurrent duplicate retry safely; do not mask unrelated DB failures.
        concurrent = db.get(Event, payload.event_id)
        if concurrent is not None and concurrent.session_id == session_id and _same_payload(concurrent, payload):
            return concurrent, True
        raise HTTPException(status_code=409, detail="Could not store event due to a conflicting event_id")
    except Exception:
        db.rollback()
        raise
    db.refresh(entity)
    return entity, False


def list_session_events(
    db: Session,
    session_id: UUID,
    principal: User | ServicePrincipal,
    event_type: EventType | None,
    severity: Severity | None,
    source: EventSource | None,
    from_dt: datetime | None,
    to_dt: datetime | None,
    page: int,
    page_size: int,
):
    get_accessible_session(db, session_id, principal)
    query = select(Event).where(Event.session_id == session_id)
    if event_type:
        query = query.where(Event.event_type == event_type)
    if severity:
        query = query.where(Event.severity == severity)
    if source:
        query = query.where(Event.source == source)
    if from_dt:
        query = query.where(Event.occurred_at >= from_dt)
    if to_dt:
        query = query.where(Event.occurred_at < to_dt)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.order_by(Event.occurred_at.desc(), Event.received_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return items, total


def build_session_report(db: Session, session: LearningSession) -> dict:
    events = db.scalars(select(Event).where(Event.session_id == session.session_id)).all()
    counts_by_type: dict[str, int] = {}
    counts_by_severity = {severity.value: 0 for severity in Severity}
    for event in events:
        counts_by_type[event.event_type.value] = counts_by_type.get(event.event_type.value, 0) + 1
        counts_by_severity[event.severity.value] += 1
    from app.services.session_service import session_duration_ms
    return {
        "session_id": session.session_id,
        "session_type": session.session_type,
        "status": session.status,
        "started_at": session.started_at,
        "ended_at": session.ended_at,
        "duration_ms": session_duration_ms(session),
        "event_count": len(events),
        "counts_by_type": counts_by_type,
        "counts_by_severity": counts_by_severity,
    }
