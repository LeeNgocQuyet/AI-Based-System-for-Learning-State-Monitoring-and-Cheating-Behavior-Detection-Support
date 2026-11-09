from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Enum as SAEnum, ForeignKey, Index, func, Uuid, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import SessionStatus, SessionType


def enum_values(enum_cls):
    return [item.value for item in enum_cls]


class LearningSession(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint("accumulated_active_ms >= 0", name="ck_sessions_duration_nonnegative"),
        CheckConstraint("((status = 'ACTIVE' AND active_started_at IS NOT NULL AND paused_at IS NULL AND ended_at IS NULL) OR (status = 'PAUSED' AND active_started_at IS NULL AND paused_at IS NOT NULL AND ended_at IS NULL) OR (status = 'ENDED' AND active_started_at IS NULL AND paused_at IS NULL AND ended_at IS NOT NULL))", name="ck_sessions_state_timestamps"),
        CheckConstraint("ended_at IS NULL OR ended_at >= started_at", name="ck_sessions_end_after_start"),
        Index("ix_sessions_learner_started", "learner_id", text("started_at DESC")),
        Index("ix_sessions_status_started", "status", text("started_at DESC")),
        Index("ix_sessions_type_status", "session_type", "status"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    learner_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT"), nullable=False)
    session_type: Mapped[SessionType] = mapped_column(SAEnum(SessionType, name="session_type", values_callable=enum_values, native_enum=True), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(SAEnum(SessionStatus, name="session_status", values_callable=enum_values, native_enum=True), nullable=False, default=SessionStatus.ACTIVE)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    paused_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    active_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accumulated_active_ms: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
