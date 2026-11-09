from __future__ import annotations


def create_learning_session(client, headers):
    response = client.post("/api/v1/sessions", json={"session_type": "LEARNING"}, headers=headers)
    assert response.status_code == 201, response.text
    return response.json()["data"]["session_id"]


def test_create_session_derives_owner_from_token(test_context):
    ctx = test_context
    session_id = create_learning_session(ctx["client"], {"Authorization": f"Bearer {ctx['learner_a_token']}"})
    from app.models import LearningSession
    from uuid import UUID
    row = ctx["db"].get(LearningSession, UUID(session_id))
    assert row.learner_id == ctx["learner_a"].user_id
    assert row.status.value == "ACTIVE"


def test_instructor_cannot_create_session(test_context):
    response = test_context["client"].post(
        "/api/v1/sessions", json={"session_type": "EXAM"},
        headers={"Authorization": f"Bearer {test_context['instructor_token']}"},
    )
    assert response.status_code == 403


def test_learner_cannot_read_other_learner_session(test_context):
    ctx = test_context
    session_id = create_learning_session(ctx["client"], {"Authorization": f"Bearer {ctx['learner_a_token']}"})
    response = ctx["client"].get(
        f"/api/v1/sessions/{session_id}",
        headers={"Authorization": f"Bearer {ctx['learner_b_token']}"},
    )
    assert response.status_code == 404


def test_pause_resume_end_lifecycle(test_context):
    ctx = test_context
    headers = {"Authorization": f"Bearer {ctx['learner_a_token']}"}
    session_id = create_learning_session(ctx["client"], headers)

    paused = ctx["client"].patch(f"/api/v1/sessions/{session_id}/status", json={"status": "PAUSED"}, headers=headers)
    assert paused.status_code == 200, paused.text
    assert paused.json()["data"]["status"] == "PAUSED"

    resumed = ctx["client"].post(f"/api/v1/sessions/{session_id}/start", headers=headers)
    assert resumed.status_code == 200, resumed.text
    assert resumed.json()["data"]["status"] == "ACTIVE"

    ended = ctx["client"].post(f"/api/v1/sessions/{session_id}/end", headers=headers)
    assert ended.status_code == 200, ended.text
    assert ended.json()["data"]["status"] == "ENDED"
    assert ended.json()["data"]["ended_at"] is not None

    cannot_restart = ctx["client"].post(f"/api/v1/sessions/{session_id}/start", headers=headers)
    assert cannot_restart.status_code == 409


def test_missing_bearer_token_is_rejected(test_context):
    response = test_context["client"].post("/api/v1/sessions", json={"session_type": "LEARNING"})
    assert response.status_code == 401


def test_instructor_list_only_granted_sessions(test_context):
    from uuid import UUID
    from app.models import InstructorSessionAccess
    ctx = test_context
    session_id = create_learning_session(ctx["client"], {"Authorization": f"Bearer {ctx['learner_a_token']}"})
    headers = {"Authorization": f"Bearer {ctx['instructor_token']}"}

    before = ctx["client"].get("/api/v1/teacher/sessions", headers=headers)
    assert before.status_code == 200
    assert before.json()["total"] == 0

    ctx["db"].add(InstructorSessionAccess(instructor_id=ctx["instructor"].user_id, session_id=UUID(session_id)))
    ctx["db"].commit()
    after = ctx["client"].get("/api/v1/teacher/sessions", headers=headers)
    assert after.status_code == 200
    assert after.json()["total"] == 1
    assert after.json()["data"][0]["session_id"] == session_id


def test_swagger_openapi_document_is_available(test_context):
    response = test_context["client"].get("/api/v1/openapi.json")
    assert response.status_code == 200
    document = response.json()
    assert document["openapi"].startswith("3.1")
    assert "/api/v1/sessions" in document["paths"]
    assert "/api/v1/sessions/{session_id}/events" in document["paths"]

    docs_page = test_context["client"].get("/api/v1/docs")
    assert docs_page.status_code == 200
