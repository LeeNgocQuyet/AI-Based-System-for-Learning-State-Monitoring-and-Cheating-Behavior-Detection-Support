from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InstructorSessionAccess(Base):
    __tablename__ = "instructor_session_access"

    instructor_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("sessions.session_id", ondelete="CASCADE"), primary_key=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
