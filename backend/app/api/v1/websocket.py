from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_principal
from app.core.security import ServicePrincipal
from app.models import User
from app.models.enums import UserRole
from app.realtime.manager import connection_manager
from app.services.session_service import get_accessible_session

router = APIRouter(tags=["Realtime WebSocket"])


def _principal_from_query_token(token: str, db: Session) -> User | ServicePrincipal:
    """Reuse the same JWT validation and account-status checks as REST APIs."""
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    return get_principal(credentials=credentials, db=db)


@router.websocket("/ws/sessions/{session_id}")
async def learner_session_stream(
    websocket: WebSocket,
    session_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    token: str | None = Query(default=None, description="Short-lived learner access token for the MVP WebSocket handshake"),
):
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        principal = _principal_from_query_token(token, db)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    if not isinstance(principal, User) or principal.role != UserRole.LEARNER:
        await websocket.close(code=1008, reason="Learner role required")
        return

    try:
        get_accessible_session(db, session_id, principal)
    except HTTPException:
        await websocket.close(code=1008, reason="Session is not accessible")
        return

    # Do not keep a DB transaction open for the lifetime of the socket.
    db.rollback()
    await websocket.accept()
    connection_manager.connect_session(session_id, websocket)
    await websocket.send_json({
        "type": "connection.ready",
        "channel": "session",
        "session_id": str(session_id),
        "replay_available": False,
    })

    try:
        while True:
            incoming = await websocket.receive_text()
            if incoming.strip().lower() == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect_session(session_id, websocket)


@router.websocket("/ws/teacher/live")
async def instructor_live_stream(
    websocket: WebSocket,
    db: Annotated[Session, Depends(get_db)],
    token: str | None = Query(default=None, description="Short-lived instructor access token for the MVP WebSocket handshake"),
):
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return

    try:
        principal = _principal_from_query_token(token, db)
    except HTTPException:
        await websocket.close(code=1008, reason="Invalid or expired token")
        return

    if not isinstance(principal, User) or principal.role != UserRole.INSTRUCTOR:
        await websocket.close(code=1008, reason="Instructor role required")
        return

    db.rollback()
    await websocket.accept()
    connection_manager.connect_teacher(principal.user_id, websocket)
    await websocket.send_json({
        "type": "connection.ready",
        "channel": "teacher",
        "instructor_id": str(principal.user_id),
        "replay_available": False,
    })

    try:
        while True:
            incoming = await websocket.receive_text()
            if incoming.strip().lower() == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect_teacher(principal.user_id, websocket)
