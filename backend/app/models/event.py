from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Index, JSON, Numeric, String, func, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import EventSource, EventType, Severity


def enum_values(enum_cls):
    return [item.value for item in enum_cls]


json_type = JSON().with_variant(JSONB, "postgresql")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("duration_ms IS NULL OR duration_ms >= 0", name="ck_events_duration_nonnegative"),
        CheckConstraint("confidence IS NULL OR (confidence >= 0 AND confidence <= 1)", name="ck_events_confidence_range"),
        CheckConstraint("schema_version = '1.0.0'", name="ck_events_schema_version"),
        CheckConstraint("((event_type IN ('EYES_CLOSED_LONG', 'YAWN_DETECTED', 'HEAD_NOD_DETECTED') AND source = 'AI_LEARNING') OR (event_type IN ('LOOK_AWAY_DETECTED', 'FACE_NOT_DETECTED') AND source IN ('AI_LEARNING', 'AI_EXAM')) OR (event_type IN ('MULTIPLE_FACES_DETECTED', 'PHONE_DETECTED') AND source = 'AI_EXAM') OR (event_type IN ('TAB_HIDDEN', 'CAMERA_LOST') AND source = 'BROWSER') OR (event_type = 'CONNECTION_LOST' AND source = 'SYSTEM'))", name="ck_events_source_matches_type"),
        Index("ix_events_session_occurred", "session_id", text("occurred_at DESC"), text("received_at DESC")),
        Index("ix_events_session_severity", "session_id", "severity"),
        Index("ix_events_type_occurred", "event_type", text("occurred_at DESC")),
    )

    event_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sessions.session_id", ondelete="RESTRICT"), nullable=False)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0.0")
    event_type: Mapped[EventType] = mapped_column(SAEnum(EventType, name="event_type", values_callable=enum_values, native_enum=True), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    source: Mapped[EventSource] = mapped_column(SAEnum(EventSource, name="event_source", values_callable=enum_values, native_enum=True), nullable=False)
    severity: Mapped[Severity] = mapped_column(SAEnum(Severity, name="event_severity", values_callable=enum_values, native_enum=True), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 4), nullable=True)
    message: Mapped[str] = mapped_column(String(500), nullable=False)
    is_reviewed: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", json_type, nullable=False, default=dict)
