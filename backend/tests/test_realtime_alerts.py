from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest
from starlette.websockets import WebSocketDisconnect

from app.models import InstructorSessionAccess
from app.realtime.manager import connection_manager
from app.services.alert_service import AlertCooldown, alert_cooldown


@pytest.fixture(autouse=True)
def reset_realtime_state():
    connection_manager.reset()
    alert_cooldown.reset()
    yield
    connection_manager.reset()
    alert_cooldown.reset()


def create_learning_session(ctx) -> str:
    response = ctx["client"].post(
        "/api/v1/sessions",
        json={"session_type": "LEARNING"},
        headers={"Authorization": f"Bearer {ctx['learner_a_token']}"},
    )
    assert response.status_code == 201, response.text
    return response.json()["data"]["session_id"]


def browser_event(session_id: str) -> dict:
    return {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "session_id": session_id,
        "event_type": "TAB_HIDDEN",
        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "BROWSER",
        "metadata": {"visibility_state": "hidden"},
    }


def test_alert_cooldown_is_per_session_and_event_type():
    cooldown = AlertCooldown(15)
    session_a = uuid4()
    session_b = uuid4()
    now = datetime(2026, 11, 15, 4, 0, tzinfo=timezone.utc)

    assert cooldown.should_emit(session_a, "TAB_HIDDEN", "MEDIUM", now)
    assert not cooldown.should_emit(session_a, "TAB_HIDDEN", "MEDIUM", now + timedelta(seconds=5))
    assert cooldown.should_emit(session_a, "CAMERA_LOST", "HIGH", now + timedelta(seconds=5))
    assert cooldown.should_emit(session_b, "TAB_HIDDEN", "MEDIUM", now + timedelta(seconds=5))
    assert cooldown.should_emit(session_a, "TAB_HIDDEN", "MEDIUM", now + timedelta(seconds=16))
    assert not cooldown.should_emit(session_a, "TAB_HIDDEN", "INFO", now + timedelta(seconds=40))


def test_learner_websocket_receives_event_stream_and_alert(test_context):
    ctx = test_context
    session_id = create_learning_session(ctx)
    token = ctx["learner_a_token"]

    with ctx["client"].websocket_connect(
        f"/api/v1/ws/sessions/{session_id}?token={token}"
    ) as websocket:
        ready = websocket.receive_json()
        assert ready["type"] == "connection.ready"
        assert ready["channel"] == "session"

        response = ctx["client"].post(
            f"/api/v1/sessions/{session_id}/events",
            json=browser_event(session_id),
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201, response.text
        assert websocket.receive_json()["type"] == "event.created"
        alert = websocket.receive_json()
        assert alert["type"] == "alert.triggered"
        assert alert["cooldown_seconds"] == alert_cooldown.cooldown_seconds


def test_cooldown_suppresses_only_alert_not_event_stream_or_database(test_context):
    ctx = test_context
    session_id = create_learning_session(ctx)
    token = ctx["learner_a_token"]
    headers = {"Authorization": f"Bearer {token}"}

    with ctx["client"].websocket_connect(
        f"/api/v1/ws/sessions/{session_id}?token={token}"
    ) as websocket:
        assert websocket.receive_json()["type"] == "connection.ready"

        first = ctx["client"].post(
            f"/api/v1/sessions/{session_id}/events",
            json=browser_event(session_id),
            headers=headers,
        )
        assert first.status_code == 201, first.text
        assert websocket.receive_json()["type"] == "event.created"
        assert websocket.receive_json()["type"] == "alert.triggered"

        second = ctx["client"].post(
            f"/api/v1/sessions/{session_id}/events",
            json=browser_event(session_id),
            headers=headers,
        )
        assert second.status_code == 201, second.text
        assert websocket.receive_json()["type"] == "event.created"

        # A second alert must not arrive during cooldown, but the event is durable.
        events = ctx["client"].get(
            f"/api/v1/sessions/{session_id}/events",
            headers=headers,
        )
        assert events.status_code == 200, events.text
        assert events.json()["total"] == 2


def test_instructor_live_stream_receives_only_granted_session_events(test_context):
    ctx = test_context
    session_id = create_learning_session(ctx)
    ctx["db"].add(
        InstructorSessionAccess(
            instructor_id=ctx["instructor"].user_id,
            session_id=UUID(session_id),
        )
    )
    ctx["db"].commit()

    token = ctx["instructor_token"]
    with ctx["client"].websocket_connect(
        f"/api/v1/ws/teacher/live?token={token}"
    ) as websocket:
        ready = websocket.receive_json()
        assert ready["type"] == "connection.ready"
        assert ready["channel"] == "teacher"

        payload = {
            "event_id": str(uuid4()),
            "schema_version": "1.0.0",
            "session_id": session_id,
            "event_type": "EYES_CLOSED_LONG",
            "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": "AI_LEARNING",
            "duration_ms": 4200,
            "confidence": 0.94,
            "metadata": {"eye_closure_ms": 4200},
        }
        response = ctx["client"].post(
            f"/api/v1/sessions/{session_id}/events",
            json=payload,
            headers={"Authorization": f"Bearer {ctx['ai_learning_token']}"},
        )
        assert response.status_code == 201, response.text
        assert websocket.receive_json()["type"] == "event.created"
        assert websocket.receive_json()["type"] == "alert.triggered"


def test_learner_cannot_subscribe_to_another_learners_session(test_context):
    ctx = test_context
    session_id = create_learning_session(ctx)

    with pytest.raises(WebSocketDisconnect):
        with ctx["client"].websocket_connect(
            f"/api/v1/ws/sessions/{session_id}?token={ctx['learner_b_token']}"
        ):
            pass


def test_instructor_role_cannot_use_learner_session_channel(test_context):
    ctx = test_context
    session_id = create_learning_session(ctx)

    with pytest.raises(WebSocketDisconnect):
        with ctx["client"].websocket_connect(
            f"/api/v1/ws/sessions/{session_id}?token={ctx['instructor_token']}"
        ):
            pass
