from __future__ import annotations

import os
os.environ.setdefault("JWT_SECRET", "pytest-only-secret-keep-this-out-of-production-123456789")
os.environ.setdefault("DATABASE_URL", "sqlite:///./test-placeholder.db")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.core.security import create_user_access_token, create_service_token, hash_password
from app.models import InstructorSessionAccess, User
from app.models.enums import AccountStatus, EventSource, UserRole


@pytest.fixture
def test_context():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    learner_a = User(email="learner.a@example.edu", full_name="Learner A", password_hash=hash_password("Unused-Test-Password1!"), role=UserRole.LEARNER, status=AccountStatus.ACTIVE)
    learner_b = User(email="learner.b@example.edu", full_name="Learner B", password_hash=hash_password("Unused-Test-Password1!"), role=UserRole.LEARNER, status=AccountStatus.ACTIVE)
    instructor = User(email="instructor@example.edu", full_name="Instructor", password_hash=hash_password("Unused-Test-Password1!"), role=UserRole.INSTRUCTOR, status=AccountStatus.ACTIVE)
    db.add_all([learner_a, learner_b, instructor])
    db.commit()
    db.refresh(learner_a)
    db.refresh(learner_b)
    db.refresh(instructor)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    context = {
        "engine": engine,
        "db": db,
        "client": client,
        "learner_a": learner_a,
        "learner_b": learner_b,
        "instructor": instructor,
        "learner_a_token": create_user_access_token(learner_a.user_id),
        "learner_b_token": create_user_access_token(learner_b.user_id),
        "instructor_token": create_user_access_token(instructor.user_id),
        "ai_learning_token": create_service_token("test-ai-learning", {EventSource.AI_LEARNING}),
        "ai_exam_token": create_service_token("test-ai-exam", {EventSource.AI_EXAM}),
        "system_token": create_service_token("test-system", {EventSource.SYSTEM}),
    }
    try:
        yield context
    finally:
        app.dependency_overrides.clear()
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def learner_headers(test_context):
    return {"Authorization": f"Bearer {test_context['learner_a_token']}"}
