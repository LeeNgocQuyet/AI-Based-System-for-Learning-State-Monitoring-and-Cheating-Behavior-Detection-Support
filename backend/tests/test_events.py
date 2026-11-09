from __future__ import annotations

from uuid import uuid4


def create_session(ctx):
    response = ctx["client"].post(
        "/api/v1/sessions", json={"session_type": "LEARNING"},
        headers={"Authorization": f"Bearer {ctx['learner_a_token']}"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["session_id"]


def browser_payload(session_id, event_id=None):
    from datetime import datetime, timezone
    return {
        "event_id": str(event_id or uuid4()),
        "schema_version": "1.0.0",
        "session_id": session_id,
        "event_type": "TAB_HIDDEN",
        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "BROWSER",
        "metadata": {"visibility_state": "hidden"},
    }


def test_post_and_get_browser_event(test_context):
    ctx = test_context
    session_id = create_session(ctx)
    headers = {"Authorization": f"Bearer {ctx['learner_a_token']}"}
    response = ctx["client"].post(f"/api/v1/sessions/{session_id}/events", json=browser_payload(session_id), headers=headers)
    assert response.status_code == 201, response.text
    event = response.json()["data"]
    assert event["source"] == "BROWSER"
    assert event["severity"] == "MEDIUM"
    assert event["received_at"]
    assert "message" in event

    listed = ctx["client"].get(f"/api/v1/sessions/{session_id}/events", headers=headers)
    assert listed.status_code == 200, listed.text
    assert listed.json()["total"] == 1
    assert listed.json()["data"][0]["event_id"] == event["event_id"]


def test_event_retry_is_idempotent_and_mismatch_conflicts(test_context):
    ctx = test_context
    session_id = create_session(ctx)
    headers = {"Authorization": f"Bearer {ctx['learner_a_token']}"}
    payload = browser_payload(session_id)
    url = f"/api/v1/sessions/{session_id}/events"

    first = ctx["client"].post(url, json=payload, headers=headers)
    second = ctx["client"].post(url, json=payload, headers=headers)
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["data"]["event_id"] == second.json()["data"]["event_id"]

    changed = {**payload, "metadata": {"visibility_state": "visible"}}
    mismatch = ctx["client"].post(url, json=changed, headers=headers)
    assert mismatch.status_code == 409


def test_user_cannot_spoof_ai_source(test_context):
    ctx = test_context
    session_id = create_session(ctx)
    payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "session_id": session_id,
        "event_type": "EYES_CLOSED_LONG",
        "occurred_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "AI_LEARNING",
        "duration_ms": 4200,
        "confidence": 0.94,
        "metadata": {"eye_closure_ms": 4200},
    }
    response = ctx["client"].post(
        f"/api/v1/sessions/{session_id}/events", json=payload,
        headers={"Authorization": f"Bearer {ctx['learner_a_token']}"},
    )
    assert response.status_code == 403


def test_ai_service_can_post_only_its_allowed_source(test_context):
    ctx = test_context
    session_id = create_session(ctx)
    payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "session_id": session_id,
        "event_type": "EYES_CLOSED_LONG",
        "occurred_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "AI_LEARNING",
        "duration_ms": 4200,
        "confidence": 0.94,
        "metadata": {"eye_closure_ms": 4200},
    }
    response = ctx["client"].post(
        f"/api/v1/sessions/{session_id}/events", json=payload,
        headers={"Authorization": f"Bearer {ctx['ai_learning_token']}"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["data"]["severity"] == "MEDIUM"

    wrong_source = {**payload, "event_id": str(uuid4()), "source": "AI_EXAM"}
    rejected = ctx["client"].post(
        f"/api/v1/sessions/{session_id}/events", json=wrong_source,
        headers={"Authorization": f"Bearer {ctx['ai_learning_token']}"},
    )
    assert rejected.status_code == 422


def test_instructor_needs_explicit_grant_to_read_events(test_context):
    from app.models import InstructorSessionAccess
    from uuid import UUID
    ctx = test_context
    session_id = create_session(ctx)
    instructor_headers = {"Authorization": f"Bearer {ctx['instructor_token']}"}
    url = f"/api/v1/sessions/{session_id}/events"
    denied = ctx["client"].get(url, headers=instructor_headers)
    assert denied.status_code == 404

    ctx["db"].add(InstructorSessionAccess(instructor_id=ctx["instructor"].user_id, session_id=UUID(session_id)))
    ctx["db"].commit()
    allowed = ctx["client"].get(url, headers=instructor_headers)
    assert allowed.status_code == 200


def test_event_rejected_after_session_ended(test_context):
    ctx = test_context
    session_id = create_session(ctx)
    headers = {"Authorization": f"Bearer {ctx['learner_a_token']}"}
    ended = ctx["client"].post(f"/api/v1/sessions/{session_id}/end", headers=headers)
    assert ended.status_code == 200
    rejected = ctx["client"].post(
        f"/api/v1/sessions/{session_id}/events", json=browser_payload(session_id), headers=headers,
    )
    assert rejected.status_code == 409


def test_client_cannot_send_backend_managed_severity(test_context):
    ctx = test_context
    session_id = create_session(ctx)
    payload = browser_payload(session_id)
    payload["severity"] = "HIGH"
    response = ctx["client"].post(
        f"/api/v1/sessions/{session_id}/events", json=payload,
        headers={"Authorization": f"Bearer {ctx['learner_a_token']}"},
    )
    assert response.status_code == 422


def test_idempotency_does_not_leak_event_to_another_learner(test_context):
    ctx = test_context
    session_id = create_session(ctx)
    owner_headers = {"Authorization": f"Bearer {ctx['learner_a_token']}"}
    payload = browser_payload(session_id)
    posted = ctx["client"].post(f"/api/v1/sessions/{session_id}/events", json=payload, headers=owner_headers)
    assert posted.status_code == 201

    # A different learner knows/reuses the event UUID but cannot read the existing event.
    denied = ctx["client"].post(
        f"/api/v1/sessions/{session_id}/events", json=payload,
        headers={"Authorization": f"Bearer {ctx['learner_b_token']}"},
    )
    assert denied.status_code == 404


def test_ai_exam_token_cannot_post_to_learning_session(test_context):
    ctx = test_context
    session_id = create_session(ctx)
    payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "session_id": session_id,
        "event_type": "MULTIPLE_FACES_DETECTED",
        "occurred_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "AI_EXAM",
        "confidence": 0.91,
        "metadata": {"face_count": 2},
    }
    response = ctx["client"].post(
        f"/api/v1/sessions/{session_id}/events", json=payload,
        headers={"Authorization": f"Bearer {ctx['ai_exam_token']}"},
    )
    assert response.status_code == 403


def test_session_report_aggregates_mock_event_types_and_severity(test_context):
    ctx = test_context
    session_id = create_session(ctx)
    headers = {"Authorization": f"Bearer {ctx['learner_a_token']}"}
    payload = browser_payload(session_id)
    posted = ctx["client"].post(f"/api/v1/sessions/{session_id}/events", json=payload, headers=headers)
    assert posted.status_code == 201

    report = ctx["client"].get(f"/api/v1/sessions/{session_id}/report", headers=headers)
    assert report.status_code == 200, report.text
    body = report.json()["data"]
    assert body["event_count"] == 1
    assert body["counts_by_type"]["TAB_HIDDEN"] == 1
    assert body["counts_by_severity"]["MEDIUM"] == 1


def test_ai_exam_token_can_post_to_exam_session(test_context):
    ctx = test_context
    response = ctx["client"].post(
        "/api/v1/sessions", json={"session_type": "EXAM"},
        headers={"Authorization": f"Bearer {ctx['learner_a_token']}"},
    )
    assert response.status_code == 201
    session_id = response.json()["data"]["session_id"]
    payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "session_id": session_id,
        "event_type": "MULTIPLE_FACES_DETECTED",
        "occurred_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "AI_EXAM",
        "confidence": 0.91,
        "metadata": {"face_count": 2},
    }
    posted = ctx["client"].post(
        f"/api/v1/sessions/{session_id}/events", json=payload,
        headers={"Authorization": f"Bearer {ctx['ai_exam_token']}"},
    )
    assert posted.status_code == 201, posted.text
    assert posted.json()["data"]["severity"] == "HIGH"


def test_phone_detection_is_disabled_by_default(test_context):
    ctx = test_context
    response = ctx["client"].post(
        "/api/v1/sessions", json={"session_type": "EXAM"},
        headers={"Authorization": f"Bearer {ctx['learner_a_token']}"},
    )
    session_id = response.json()["data"]["session_id"]
    payload = {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "session_id": session_id,
        "event_type": "PHONE_DETECTED",
        "occurred_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "AI_EXAM",
        "confidence": 0.86,
        "metadata": {"object_count": 1},
    }
    blocked = ctx["client"].post(
        f"/api/v1/sessions/{session_id}/events", json=payload,
        headers={"Authorization": f"Bearer {ctx['ai_exam_token']}"},
    )
    assert blocked.status_code == 403
