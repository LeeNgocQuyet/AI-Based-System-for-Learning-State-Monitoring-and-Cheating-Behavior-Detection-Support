from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import require_instructor
from app.db.session import get_db
from app.models import Event, User
from app.models.enums import SessionStatus, SessionType, Severity
from app.schemas.session import TeacherSessionListOut, TeacherSessionOut
from app.services.session_service import as_utc, list_instructor_sessions, session_duration_ms

router = APIRouter(prefix="/teacher", tags=["Teacher"])


@router.get("/sessions", response_model=TeacherSessionListOut, summary="List sessions granted to current instructor")
def get_teacher_sessions(
    instructor: Annotated[User, Depends(require_instructor)],
    db: Annotated[Session, Depends(get_db)],
    session_type: SessionType | None = None,
    status_filter: SessionStatus | None = Query(default=None, alias="status"),
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    if from_dt and to_dt and from_dt >= to_dt:
        raise HTTPException(status_code=422, detail="from must be earlier than to")
    rows, total = list_instructor_sessions(db, instructor, session_type, status_filter, from_dt, to_dt, page, page_size)
    data = []
    for session, learner in rows:
        counts = db.execute(
            select(func.count(Event.event_id), func.count(Event.event_id).filter(Event.severity == Severity.HIGH))
            .where(Event.session_id == session.session_id)
        ).one()
        data.append(TeacherSessionOut(
            session_id=session.session_id,
            session_type=session.session_type.value,
            status=session.status.value,
            started_at=as_utc(session.started_at),
            ended_at=as_utc(session.ended_at),
            duration_ms=session_duration_ms(session),
            learner_id=learner.user_id,
            learner_display_name=learner.full_name,
            event_count=int(counts[0] or 0),
            high_severity_count=int(counts[1] or 0),
        ))
    return {"data": data, "page": page, "page_size": page_size, "total": total}
