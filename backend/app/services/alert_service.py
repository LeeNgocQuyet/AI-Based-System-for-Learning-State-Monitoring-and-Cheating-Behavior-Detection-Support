from __future__ import annotations

from datetime import datetime, timezone
from threading import Lock
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Event, InstructorSessionAccess
from app.models.enums import Severity
from app.realtime.manager import connection_manager


class AlertCooldown:
    """Presentation-only cooldown keyed by (session_id, event_type)."""

    def __init__(self, cooldown_seconds: int) -> None:
        if cooldown_seconds < 0:
            raise ValueError("cooldown_seconds cannot be negative")
        self.cooldown_seconds = cooldown_seconds
        self._last_alerted: dict[tuple[UUID, str], datetime] = {}
        self._lock = Lock()

    def should_emit(
        self,
        session_id: UUID,
        event_type: str,
        severity: str,
        now: datetime | None = None,
    ) -> bool:
        if severity == Severity.INFO.value:
            return False

        current_time = now or datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        else:
            current_time = current_time.astimezone(timezone.utc)

        key = (session_id, event_type)
        with self._lock:
            previous = self._last_alerted.get(key)
            if previous is not None and self.cooldown_seconds > 0:
                elapsed = (current_time - previous).total_seconds()
                if elapsed < self.cooldown_seconds:
                    return False

            self._last_alerted[key] = current_time

            # Bound memory use during long-running local demos.
            if len(self._last_alerted) > 5000:
                cutoff = current_time.timestamp() - max(self.cooldown_seconds, 1) * 4
                self._last_alerted = {
                    item_key: item_time
                    for item_key, item_time in self._last_alerted.items()
                    if item_time.timestamp() >= cutoff
                }
            return True

    def reset(self) -> None:
        with self._lock:
            self._last_alerted.clear()


alert_cooldown = AlertCooldown(settings.alert_cooldown_seconds)


async def publish_event(db: Session, event: Event, event_payload: dict) -> None:
    """Publish every persisted event, then optionally publish a UI alert.

    Cooldown never suppresses database writes or the event.created stream. It
    only limits alert.triggered notifications to connected clients.
    """
    session_id = event.session_id
    instructor_ids = set(
        db.scalars(
            select(InstructorSessionAccess.instructor_id).where(
                InstructorSessionAccess.session_id == session_id
            )
        ).all()
    )

    event_message = {
        "type": "event.created",
        "session_id": str(session_id),
        "data": event_payload,
    }
    await connection_manager.broadcast_session(session_id, event_message)
    await connection_manager.broadcast_teachers(instructor_ids, event_message)

    has_recipients = (
        connection_manager.has_session_subscribers(session_id)
        or connection_manager.has_teacher_subscribers(instructor_ids)
    )
    if not has_recipients:
        return

    # received_at is assigned by Backend when the event is committed.
    if not alert_cooldown.should_emit(
        session_id=session_id,
        event_type=event.event_type.value,
        severity=event.severity.value,
        now=event.received_at,
    ):
        return

    alert_message = {
        "type": "alert.triggered",
        "session_id": str(session_id),
        "cooldown_seconds": alert_cooldown.cooldown_seconds,
        "data": event_payload,
    }
    await connection_manager.broadcast_session(session_id, alert_message)
    await connection_manager.broadcast_teachers(instructor_ids, alert_message)
