from __future__ import annotations

import asyncio
from threading import RLock
from typing import Any
from uuid import UUID

from fastapi import WebSocket


class RealtimeConnectionManager:
    """In-process WebSocket registry for a single-worker MVP deployment.

    Events remain durable in PostgreSQL. This manager only handles best-effort
    live delivery; reconnecting clients use the REST event query for catch-up.
    """

    def __init__(self) -> None:
        self._session_connections: dict[UUID, set[WebSocket]] = {}
        self._teacher_connections: dict[UUID, set[WebSocket]] = {}
        self._lock = RLock()

    def connect_session(self, session_id: UUID, websocket: WebSocket) -> None:
        with self._lock:
            self._session_connections.setdefault(session_id, set()).add(websocket)

    def disconnect_session(self, session_id: UUID, websocket: WebSocket) -> None:
        with self._lock:
            connections = self._session_connections.get(session_id)
            if connections is not None:
                connections.discard(websocket)
                if not connections:
                    self._session_connections.pop(session_id, None)

    def connect_teacher(self, instructor_id: UUID, websocket: WebSocket) -> None:
        with self._lock:
            self._teacher_connections.setdefault(instructor_id, set()).add(websocket)

    def disconnect_teacher(self, instructor_id: UUID, websocket: WebSocket) -> None:
        with self._lock:
            connections = self._teacher_connections.get(instructor_id)
            if connections is not None:
                connections.discard(websocket)
                if not connections:
                    self._teacher_connections.pop(instructor_id, None)

    def has_session_subscribers(self, session_id: UUID) -> bool:
        with self._lock:
            return bool(self._session_connections.get(session_id))

    def has_teacher_subscribers(self, instructor_ids: set[UUID]) -> bool:
        with self._lock:
            return any(self._teacher_connections.get(user_id) for user_id in instructor_ids)

    def _remove_socket(self, websocket: WebSocket) -> None:
        with self._lock:
            for registry in (self._session_connections, self._teacher_connections):
                for key, connections in list(registry.items()):
                    connections.discard(websocket)
                    if not connections:
                        registry.pop(key, None)

    async def _send_one(self, websocket: WebSocket, payload: dict[str, Any]) -> None:
        try:
            await websocket.send_json(payload)
        except Exception:
            # A disconnected client must not block delivery to other subscribers.
            self._remove_socket(websocket)

    async def _broadcast(self, sockets: set[WebSocket], payload: dict[str, Any]) -> None:
        if sockets:
            await asyncio.gather(
                *(self._send_one(websocket, payload) for websocket in sockets),
                return_exceptions=True,
            )

    async def broadcast_session(self, session_id: UUID, payload: dict[str, Any]) -> None:
        with self._lock:
            sockets = set(self._session_connections.get(session_id, set()))
        await self._broadcast(sockets, payload)

    async def broadcast_teachers(
        self,
        instructor_ids: set[UUID],
        payload: dict[str, Any],
    ) -> None:
        with self._lock:
            sockets: set[WebSocket] = set()
            for instructor_id in instructor_ids:
                sockets.update(self._teacher_connections.get(instructor_id, set()))
        await self._broadcast(sockets, payload)

    def reset(self) -> None:
        """Clear connection state; intended for automated tests and shutdown."""
        with self._lock:
            self._session_connections.clear()
            self._teacher_connections.clear()


connection_manager = RealtimeConnectionManager()
