"""
test_security_reliability.py — Backend Quality v1.4
Kiểm thử phân quyền (Auth/RBAC), tính tin cậy WebSocket và log kết nối.
Chạy: pytest -q   (từ thư mục backend/)
Dùng SQLite in-memory qua fixture test_context trong conftest.py.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from starlette.websockets import WebSocketDisconnect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_session(ctx: dict) -> str:
    """Tạo một LEARNING session bằng learner_a và trả về session_id."""
    r = ctx["client"].post(
        "/api/v1/sessions",
        json={"session_type": "LEARNING"},
        headers={"Authorization": f"Bearer {ctx['learner_a_token']}"},
    )
    assert r.status_code == 201, r.text
    return r.json()["data"]["session_id"]


def browser_event_payload(session_id: str) -> dict:
    """Tạo một TAB_HIDDEN event payload hợp lệ cho session_id."""
    return {
        "event_id": str(uuid4()),
        "schema_version": "1.0.0",
        "session_id": session_id,
        "event_type": "TAB_HIDDEN",
        "occurred_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "BROWSER",
        "metadata": {"visibility_state": "hidden"},
    }


# ---------------------------------------------------------------------------
# Auth / RBAC isolation tests
# ---------------------------------------------------------------------------

class TestLearnerIsolation:
    """Learner A không được đọc dữ liệu của Learner B."""

    def test_learner_b_cannot_read_a_session(self, test_context):
        """GET /sessions/{id} của A trả về 404 với token của B."""
        c = test_context
        sid = create_session(c)
        stranger = {"Authorization": f"Bearer {c['learner_b_token']}"}
        r = c["client"].get(f"/api/v1/sessions/{sid}", headers=stranger)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"

    def test_learner_b_cannot_read_a_events(self, test_context):
        """GET /sessions/{id}/events của A trả về 404 với token của B."""
        c = test_context
        sid = create_session(c)
        # Learner A nạp một event
        c["client"].post(
            f"/api/v1/sessions/{sid}/events",
            json=browser_event_payload(sid),
            headers={"Authorization": f"Bearer {c['learner_a_token']}"},
        )
        stranger = {"Authorization": f"Bearer {c['learner_b_token']}"}
        r = c["client"].get(f"/api/v1/sessions/{sid}/events", headers=stranger)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"

    def test_learner_b_cannot_read_a_report(self, test_context):
        """GET /sessions/{id}/report của A trả về 404 với token của B."""
        c = test_context
        sid = create_session(c)
        stranger = {"Authorization": f"Bearer {c['learner_b_token']}"}
        r = c["client"].get(f"/api/v1/sessions/{sid}/report", headers=stranger)
        assert r.status_code == 404, f"Expected 404, got {r.status_code}: {r.text}"

    def test_learner_b_cannot_read_a_session_events_or_report(self, test_context):
        """Kiểm tra đồng thời 3 endpoint: session, events, report."""
        c = test_context
        sid = create_session(c)
        owner = {"Authorization": f"Bearer {c['learner_a_token']}"}
        stranger = {"Authorization": f"Bearer {c['learner_b_token']}"}
        # Nạp event từ owner
        posted = c["client"].post(f"/api/v1/sessions/{sid}/events", json=browser_event_payload(sid), headers=owner)
        assert posted.status_code == 201, posted.text
        # Kiểm tra cả 3 endpoint với stranger
        for path in (
            f"/api/v1/sessions/{sid}",
            f"/api/v1/sessions/{sid}/events",
            f"/api/v1/sessions/{sid}/report",
        ):
            r = c["client"].get(path, headers=stranger)
            assert r.status_code == 404, f"{path}: expected 404, got {r.status_code} {r.text}"


class TestInstructorIsolation:
    """Instructor chỉ được đọc session có grant."""

    def test_instructor_without_grant_cannot_read_session(self, test_context):
        c = test_context
        sid = create_session(c)
        r = c["client"].get(
            f"/api/v1/sessions/{sid}",
            headers={"Authorization": f"Bearer {c['instructor_token']}"},
        )
        assert r.status_code == 404

    def test_instructor_without_grant_cannot_read_events(self, test_context):
        c = test_context
        sid = create_session(c)
        r = c["client"].get(
            f"/api/v1/sessions/{sid}/events",
            headers={"Authorization": f"Bearer {c['instructor_token']}"},
        )
        assert r.status_code == 404

    def test_instructor_without_grant_cannot_read_report(self, test_context):
        c = test_context
        sid = create_session(c)
        r = c["client"].get(
            f"/api/v1/sessions/{sid}/report",
            headers={"Authorization": f"Bearer {c['instructor_token']}"},
        )
        assert r.status_code == 404


class TestUnauthenticated:
    """Request không có token bị từ chối 401."""

    def test_no_token_sessions_mine(self, test_context):
        r = test_context["client"].get("/api/v1/sessions/mine")
        assert r.status_code == 401

    def test_no_token_create_session(self, test_context):
        r = test_context["client"].post("/api/v1/sessions", json={"session_type": "LEARNING"})
        assert r.status_code == 401

    def test_invalid_token_returns_401(self, test_context):
        r = test_context["client"].get(
            "/api/v1/sessions/mine",
            headers={"Authorization": "Bearer this-is-not-a-valid-jwt"},
        )
        assert r.status_code == 401


# ---------------------------------------------------------------------------
# WebSocket Auth / Role tests
# ---------------------------------------------------------------------------

class TestWebSocketAuth:
    """WebSocket từ chối đúng mã khi token thiếu, sai, hoặc role sai."""

    def test_rejects_missing_token(self, test_context):
        c = test_context
        sid = create_session(c)
        with pytest.raises(WebSocketDisconnect):
            with c["client"].websocket_connect(f"/api/v1/ws/sessions/{sid}"):
                pass

    def test_rejects_invalid_token(self, test_context):
        c = test_context
        sid = create_session(c)
        with pytest.raises(WebSocketDisconnect):
            with c["client"].websocket_connect(f"/api/v1/ws/sessions/{sid}?token=invalid-token"):
                pass

    def test_rejects_missing_and_invalid_token(self, test_context):
        """Hợp nhất cả hai trường hợp để gom test."""
        c = test_context
        sid = create_session(c)
        with pytest.raises(WebSocketDisconnect):
            with c["client"].websocket_connect(f"/api/v1/ws/sessions/{sid}"):
                pass
        with pytest.raises(WebSocketDisconnect):
            with c["client"].websocket_connect(f"/api/v1/ws/sessions/{sid}?token=invalid-token"):
                pass

    def test_rejects_wrong_role_instructor_on_learner_channel(self, test_context):
        """Instructor token không được dùng kênh learner."""
        c = test_context
        sid = create_session(c)
        with pytest.raises(WebSocketDisconnect):
            with c["client"].websocket_connect(
                f"/api/v1/ws/sessions/{sid}?token={c['instructor_token']}"
            ):
                pass

    def test_rejects_learner_on_teacher_channel(self, test_context):
        """Learner token không được dùng kênh teacher."""
        c = test_context
        with pytest.raises(WebSocketDisconnect):
            with c["client"].websocket_connect(
                f"/api/v1/ws/teacher/live?token={c['learner_a_token']}"
            ):
                pass

    def test_rejects_learner_b_on_session_owned_by_a(self, test_context):
        """Learner B không được subscribe vào session của Learner A qua WebSocket."""
        c = test_context
        sid = create_session(c)
        with pytest.raises(WebSocketDisconnect):
            with c["client"].websocket_connect(
                f"/api/v1/ws/sessions/{sid}?token={c['learner_b_token']}"
            ):
                pass


# ---------------------------------------------------------------------------
# WebSocket Reliability / Lifecycle tests
# ---------------------------------------------------------------------------

class TestWebSocketReliability:
    """Kiểm thử tính tin cậy: log kết nối, cleanup registry sau disconnect."""

    def test_disconnect_cleans_registry_and_logs(self, test_context, caplog):
        """Sau khi WS đóng: registry sạch, log có connected/disconnected, JWT không bị ghi."""
        from uuid import UUID
        from app.realtime.manager import connection_manager

        c = test_context
        sid = create_session(c)
        token = c["learner_a_token"]

        caplog.set_level(logging.INFO, logger="app.api.v1.websocket")
        with c["client"].websocket_connect(f"/api/v1/ws/sessions/{sid}?token={token}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "connection.ready"
            assert msg["session_id"] == sid
            # Kiểm tra registry đang có subscriber
            assert connection_manager.has_session_subscribers(UUID(sid))

        # Sau khi thoát context manager, kết nối đã đóng
        assert not connection_manager.has_session_subscribers(UUID(sid))
        # Log phải có connected và disconnected
        assert "websocket.connected" in caplog.text
        assert "websocket.disconnected" in caplog.text
        # JWT không được ghi vào log
        assert token not in caplog.text

    def test_websocket_disconnect_cleans_registry_and_logs_without_token(self, test_context, caplog):
        """Alias test khớp tên gốc từ backend-quality-v1.4 để tương thích."""
        self.test_disconnect_cleans_registry_and_logs(test_context, caplog)

    def test_ping_pong(self, test_context):
        """Gửi ping nhận được pong."""
        c = test_context
        sid = create_session(c)
        token = c["learner_a_token"]
        with c["client"].websocket_connect(f"/api/v1/ws/sessions/{sid}?token={token}") as ws:
            ws.receive_json()  # connection.ready
            ws.send_text("ping")
            msg = ws.receive_json()
            assert msg["type"] == "pong"

    def test_teacher_websocket_connect_and_disconnect(self, test_context, caplog):
        """Teacher WS: log connected/disconnected, registry cleanup."""
        from app.realtime.manager import connection_manager

        c = test_context
        token = c["instructor_token"]
        instructor_id = c["instructor"].user_id

        caplog.set_level(logging.INFO, logger="app.api.v1.websocket")
        with c["client"].websocket_connect(f"/api/v1/ws/teacher/live?token={token}") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "connection.ready"
            assert msg["channel"] == "teacher"
            assert connection_manager.has_teacher_subscribers({instructor_id})

        assert not connection_manager.has_teacher_subscribers({instructor_id})
        assert "websocket.connected" in caplog.text
        assert "websocket.disconnected" in caplog.text
        assert token not in caplog.text

    def test_rejected_ws_logs_warning(self, test_context, caplog):
        """WebSocket bị từ chối phải ghi warning log."""
        c = test_context
        sid = create_session(c)

        caplog.set_level(logging.WARNING, logger="app.api.v1.websocket")
        with pytest.raises(WebSocketDisconnect):
            with c["client"].websocket_connect(f"/api/v1/ws/sessions/{sid}"):
                pass
        assert "websocket.rejected" in caplog.text
        assert "missing_token" in caplog.text
