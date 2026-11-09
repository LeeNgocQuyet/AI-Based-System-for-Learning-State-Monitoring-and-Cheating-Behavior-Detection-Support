from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SessionTypeValue(str, Enum):
    LEARNING = "LEARNING"
    EXAM = "EXAM"


class SessionStatusValue(str, Enum):
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ENDED = "ENDED"


class SessionCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_type: SessionTypeValue


class SessionStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: SessionStatusValue


class SessionOut(BaseModel):
    session_id: UUID
    session_type: SessionTypeValue
    status: SessionStatusValue
    started_at: datetime
    ended_at: datetime | None
    duration_ms: int | None


class SessionListOut(BaseModel):
    data: list[SessionOut]
    page: int
    page_size: int
    total: int


class TeacherSessionOut(SessionOut):
    learner_id: UUID
    learner_display_name: str
    event_count: int
    high_severity_count: int


class TeacherSessionListOut(BaseModel):
    data: list[TeacherSessionOut]
    page: int
    page_size: int
    total: int


class SessionReportOut(BaseModel):
    session_id: UUID
    session_type: SessionTypeValue
    status: SessionStatusValue
    started_at: datetime
    ended_at: datetime | None
    duration_ms: int | None
    event_count: int
    counts_by_type: dict[str, int]
    counts_by_severity: dict[str, int]


class SessionReportResponse(BaseModel):
    data: SessionReportOut


class SessionResponse(BaseModel):
    data: SessionOut

