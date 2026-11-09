from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import Event, InstructorSessionAccess, LearningSession, User
from app.models.enums import (
    AccountStatus, EventSource, EventType, SessionStatus, SessionType, Severity, UserRole,
)
from app.services.event_service import EVENT_MESSAGES, normalize_severity


def required_or_default(name: str, default: str) -> str:
    return os.getenv(name, default).strip()


FALLBACK_DEMO_PASSWORDS: dict[str, str] = {
    "DEMO_LEARNER1_PASSWORD": "DemoLearnerPassword123!",
    "DEMO_LEARNER2_PASSWORD": "DemoLearnerPassword123!",
    "DEMO_INSTRUCTOR_PASSWORD": "DemoInstructorPassword123!",
}


def required_password(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value or value.startswith("REPLACE_WITH_"):
        fallback = FALLBACK_DEMO_PASSWORDS.get(name, "DemoPassword123!")
        print(f"NOTICE: {name} not set or contains placeholder; using demo password '{fallback}'", file=sys.stderr)
        return fallback
    if len(value) < 12:
        raise RuntimeError(f"{name} must contain at least 12 characters")
    return value


def get_or_create_user(db, email: str, full_name: str, role: UserRole, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None:
        user = User(
            email=email.lower(),
            full_name=full_name,
            password_hash=hash_password(password),
            role=role,
            status=AccountStatus.ACTIVE,
        )
        db.add(user)
        db.flush()
    else:
        if user.role != role:
            raise RuntimeError(f"{email} already exists with role {user.role.value}; refusing to change role")
        user.full_name = full_name
        user.status = AccountStatus.ACTIVE
        user.password_hash = hash_password(password)
    return user


def stable_uuid(value: str) -> uuid.UUID:
    return uuid.uuid5(uuid.NAMESPACE_URL, f"group3-learning-monitor:{value}")


def main() -> None:
    learner1_email = required_or_default("DEMO_LEARNER1_EMAIL", "learner.one@example.edu").lower()
    learner2_email = required_or_default("DEMO_LEARNER2_EMAIL", "learner.two@example.edu").lower()
    instructor_email = required_or_default("DEMO_INSTRUCTOR_EMAIL", "instructor.demo@example.edu").lower()
    learner1_password = required_password("DEMO_LEARNER1_PASSWORD")
    learner2_password = required_password("DEMO_LEARNER2_PASSWORD")
    instructor_password = required_password("DEMO_INSTRUCTOR_PASSWORD")

    now = datetime.now(timezone.utc)
    db = SessionLocal()
    try:
        learner1 = get_or_create_user(db, learner1_email, "Demo Learner One", UserRole.LEARNER, learner1_password)
        learner2 = get_or_create_user(db, learner2_email, "Demo Learner Two", UserRole.LEARNER, learner2_password)
        instructor = get_or_create_user(db, instructor_email, "Demo Instructor", UserRole.INSTRUCTOR, instructor_password)
        db.flush()

        learning_id = stable_uuid(f"session:{learner1_email}:learning")
        exam_id = stable_uuid(f"session:{learner2_email}:exam")

        learning = db.get(LearningSession, learning_id)
        if learning is None:
            learning = LearningSession(
                session_id=learning_id,
                learner_id=learner1.user_id,
                session_type=SessionType.LEARNING,
                status=SessionStatus.ENDED,
                started_at=now - timedelta(minutes=65),
                active_started_at=None,
                paused_at=None,
                ended_at=now - timedelta(minutes=5),
                accumulated_active_ms=60 * 60 * 1000,
            )
            db.add(learning)

        exam = db.get(LearningSession, exam_id)
        if exam is None:
            exam = LearningSession(
                session_id=exam_id,
                learner_id=learner2.user_id,
                session_type=SessionType.EXAM,
                status=SessionStatus.ACTIVE,
                started_at=now - timedelta(minutes=25),
                active_started_at=now - timedelta(minutes=25),
                paused_at=None,
                ended_at=None,
                accumulated_active_ms=0,
            )
            db.add(exam)

        db.flush()

        for session in (learning, exam):
            grant = db.get(InstructorSessionAccess, (instructor.user_id, session.session_id))
            if grant is None:
                db.add(InstructorSessionAccess(
                    instructor_id=instructor.user_id,
                    session_id=session.session_id,
                    granted_at=now - timedelta(minutes=30),
                ))

        demo_events = [
            (stable_uuid("event:learning:1"), learning_id, EventType.EYES_CLOSED_LONG, EventSource.AI_LEARNING, now - timedelta(minutes=50), 3200, 0.92, {"eye_closure_ms": 3200}),
            (stable_uuid("event:learning:2"), learning_id, EventType.YAWN_DETECTED, EventSource.AI_LEARNING, now - timedelta(minutes=42), None, 0.88, {"yawn_probability": 0.88}),
            (stable_uuid("event:learning:3"), learning_id, EventType.HEAD_NOD_DETECTED, EventSource.AI_LEARNING, now - timedelta(minutes=31), 1800, 0.86, {"nod_count": 2}),
            (stable_uuid("event:learning:4"), learning_id, EventType.LOOK_AWAY_DETECTED, EventSource.AI_LEARNING, now - timedelta(minutes=20), 4100, 0.84, {"direction": "DOWN"}),
            (stable_uuid("event:learning:5"), learning_id, EventType.CAMERA_LOST, EventSource.BROWSER, now - timedelta(minutes=10), None, None, {"reason": "USER_DISABLED"}),
            (stable_uuid("event:exam:1"), exam_id, EventType.TAB_HIDDEN, EventSource.BROWSER, now - timedelta(minutes=15), None, None, {"visibility_state": "hidden"}),
            (stable_uuid("event:exam:2"), exam_id, EventType.MULTIPLE_FACES_DETECTED, EventSource.AI_EXAM, now - timedelta(minutes=8), None, 0.91, {"face_count": 2}),
            (stable_uuid("event:exam:3"), exam_id, EventType.FACE_NOT_DETECTED, EventSource.AI_EXAM, now - timedelta(minutes=2), 5200, 0.95, {"face_count": 0}),
        ]

        for event_id, target_session_id, event_type, source, occurred_at, duration_ms, confidence, metadata in demo_events:
            if db.get(Event, event_id) is not None:
                continue
            severity = normalize_severity(event_type, duration_ms)
            db.add(Event(
                event_id=event_id,
                session_id=target_session_id,
                schema_version="1.0.0",
                event_type=event_type,
                occurred_at=occurred_at,
                received_at=occurred_at + timedelta(milliseconds=120),
                source=source,
                severity=severity,
                duration_ms=duration_ms,
                confidence=confidence,
                message=EVENT_MESSAGES[event_type],
                metadata_json=metadata,
            ))

        db.commit()
        print("Demo seed completed.")
        print(f"Learner 1: {learner1_email} (user_id={learner1.user_id})")
        print(f"Learner 2: {learner2_email} (user_id={learner2.user_id})")
        print(f"Instructor: {instructor_email} (user_id={instructor.user_id})")
        print(f"Learning session: {learning_id}")
        print(f"Exam session: {exam_id}")
        print("Instructor read grants created for both demo sessions.")
        print("Local demo passwords are documented in .env.example; change them before sharing any environment.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SEED ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
