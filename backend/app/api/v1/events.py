from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_principal
from app.core.security import ServicePrincipal
from app.db.session import get_db
from app.models import Event, User
from app.models.enums import EventSource, EventType, Severity
from app.schemas.event import EventIngest, EventListOut, EventOut, EventResponse
from app.services.event_service import ingest_event, list_session_events
from app.services.session_service import as_utc

router = APIRouter(prefix="/sessions/{session_id}/events", tags=["Events"])


def to_event_out(entity: Event) -> EventOut:
    return EventOut(
        event_id=entity.event_id,
        schema_version=entity.schema_version,
        session_id=entity.session_id,
        event_type=entity.event_type.value,
        occurred_at=as_utc(entity.occurred_at),
        received_at=as_utc(entity.received_at),
        source=entity.source.value,
        severity=entity.severity.value,
        duration_ms=entity.duration_ms,
        confidence=float(entity.confidence) if entity.confidence is not None else None,
        message=entity.message,
        is_reviewed=bool(getattr(entity, "is_reviewed", False)),
        reviewed_at=as_utc(getattr(entity, "reviewed_at", None)),
        metadata=entity.metadata_json or {},
    )


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED, responses={200: {"model": EventResponse, "description": "Exact idempotent retry; existing event returned"}}, summary="Ingest one event")
def post_event(
    session_id: UUID,
    payload: EventIngest,
    response: Response,
    principal: Annotated[User | ServicePrincipal, Depends(get_principal)],
    db: Annotated[Session, Depends(get_db)],
):
    entity, duplicate = ingest_event(db, session_id, payload, principal)
    if duplicate:
        response.status_code = status.HTTP_200_OK
    return {"data": to_event_out(entity)}


@router.get("", response_model=EventListOut, summary="List events of an accessible session")
def get_events(
    session_id: UUID,
    principal: Annotated[User | ServicePrincipal, Depends(get_principal)],
    db: Annotated[Session, Depends(get_db)],
    event_type: EventType | None = None,
    severity: Severity | None = None,
    source: EventSource | None = None,
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    if from_dt and to_dt and from_dt >= to_dt:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="from must be earlier than to")
    items, total = list_session_events(db, session_id, principal, event_type, severity, source, from_dt, to_dt, page, page_size)
    return {"data": [to_event_out(item) for item in items], "page": page, "page_size": page_size, "total": total}
