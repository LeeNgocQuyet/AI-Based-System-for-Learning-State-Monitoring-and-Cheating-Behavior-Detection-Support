from __future__ import annotations

import argparse
import sys
from pathlib import Path
from uuid import UUID

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import select
from app.db.session import SessionLocal
from app.models import InstructorSessionAccess, LearningSession, User
from app.models.enums import AccountStatus, UserRole


def main() -> None:
    parser = argparse.ArgumentParser(description="Grant an existing instructor read access to one session (local trusted operation)")
    parser.add_argument("--instructor-email", required=True)
    parser.add_argument("--session-id", required=True)
    args = parser.parse_args()
    session_id = UUID(args.session_id)

    db = SessionLocal()
    try:
        instructor = db.scalar(select(User).where(User.email == args.instructor_email.lower()))
        if instructor is None or instructor.role != UserRole.INSTRUCTOR or instructor.status != AccountStatus.ACTIVE:
            raise RuntimeError("An active INSTRUCTOR account is required")
        if db.get(LearningSession, session_id) is None:
            raise RuntimeError("Session not found")
        grant = db.get(InstructorSessionAccess, (instructor.user_id, session_id))
        if grant is None:
            db.add(InstructorSessionAccess(instructor_id=instructor.user_id, session_id=session_id))
            db.commit()
            print("Instructor access granted.")
        else:
            print("Grant already exists; no change made.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
