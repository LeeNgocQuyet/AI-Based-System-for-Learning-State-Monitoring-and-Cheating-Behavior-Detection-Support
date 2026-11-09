from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EventTypeValue(str, Enum):
    EYES_CLOSED_LONG = "EYES_CLOSED_LONG"
    YAWN_DETECTED = "YAWN_DETECTED"
    HEAD_NOD_DETECTED = "HEAD_NOD_DETECTED"
    LOOK_AWAY_DETECTED = "LOOK_AWAY_DETECTED"
    FACE_NOT_DETECTED = "FACE_NOT_DETECTED"
    MULTIPLE_FACES_DETECTED = "MULTIPLE_FACES_DETECTED"
    PHONE_DETECTED = "PHONE_DETECTED"
    TAB_HIDDEN = "TAB_HIDDEN"
    CAMERA_LOST = "CAMERA_LOST"
    CONNECTION_LOST = "CONNECTION_LOST"


class EventSourceValue(str, Enum):
    AI_LEARNING = "AI_LEARNING"
    AI_EXAM = "AI_EXAM"
    BROWSER = "BROWSER"
    SYSTEM = "SYSTEM"


class SeverityValue(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


EXPECTED_SOURCES: dict[EventTypeValue, set[EventSourceValue]] = {
    EventTypeValue.EYES_CLOSED_LONG: {EventSourceValue.AI_LEARNING},
    EventTypeValue.YAWN_DETECTED: {EventSourceValue.AI_LEARNING},
    EventTypeValue.HEAD_NOD_DETECTED: {EventSourceValue.AI_LEARNING},
    EventTypeValue.LOOK_AWAY_DETECTED: {EventSourceValue.AI_LEARNING, EventSourceValue.AI_EXAM},
    EventTypeValue.FACE_NOT_DETECTED: {EventSourceValue.AI_LEARNING, EventSourceValue.AI_EXAM},
    EventTypeValue.MULTIPLE_FACES_DETECTED: {EventSourceValue.AI_EXAM},
    EventTypeValue.PHONE_DETECTED: {EventSourceValue.AI_EXAM},
    EventTypeValue.TAB_HIDDEN: {EventSourceValue.BROWSER},
    EventTypeValue.CAMERA_LOST: {EventSourceValue.BROWSER},
    EventTypeValue.CONNECTION_LOST: {EventSourceValue.SYSTEM},
}


class EventIngest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: UUID
    schema_version: str = Field(pattern=r"^1\.0\.0$")
    session_id: UUID
    event_type: EventTypeValue
    occurred_at: datetime
    source: EventSourceValue
    duration_ms: int | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def require_utc_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("occurred_at must include a timezone and be UTC")
        if value.utcoffset().total_seconds() != 0:
            raise ValueError("occurred_at must be UTC (Z or +00:00)")
        return value.astimezone(timezone.utc)

    @model_validator(mode="after")
    def validate_source_for_event(self):
        allowed = EXPECTED_SOURCES[self.event_type]
        if self.source not in allowed:
            allowed_values = ", ".join(sorted(item.value for item in allowed))
            raise ValueError(f"source for {self.event_type.value} must be one of: {allowed_values}")
        if self.source in {EventSourceValue.BROWSER, EventSourceValue.SYSTEM} and self.confidence is not None:
            raise ValueError("confidence is only accepted for AI events")
        return self


class EventOut(BaseModel):
    event_id: UUID
    schema_version: str
    session_id: UUID
    event_type: EventTypeValue
    occurred_at: datetime
    received_at: datetime
    source: EventSourceValue
    severity: SeverityValue
    duration_ms: int | None
    confidence: float | None
    message: str
    is_reviewed: bool = False
    reviewed_at: datetime | None = None
    metadata: dict[str, Any]


class EventListOut(BaseModel):
    data: list[EventOut]
    page: int
    page_size: int
    total: int


class EventResponse(BaseModel):
    data: EventOut
