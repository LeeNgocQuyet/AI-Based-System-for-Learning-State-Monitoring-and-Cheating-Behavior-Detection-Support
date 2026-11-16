# API Contract Delta v1.3 — Realtime, Alert Cooldown & Report

This is an additive extension to Backend Session/Event API v1.2. It keeps the REST paths and event ingest schema `1.0.0` unchanged.

## 1. WebSocket endpoints

| Channel | URL | Authorization |
|---|---|---|
| Learner session | `ws://localhost:8000/api/v1/ws/sessions/{session_id}?token={access_token}` | Active `LEARNER` who owns the session |
| Instructor live | `ws://localhost:8000/api/v1/ws/teacher/live?token={access_token}` | Active `INSTRUCTOR`; events are filtered by `instructor_session_access` grants |

On connection, server sends `connection.ready`. Send text `ping` to receive `{"type":"pong"}`.

## 2. Event envelopes

Every newly committed event is sent as `event.created`. A UI alert is sent separately as `alert.triggered` when it passes cooldown. The `data` property is the Event Record response object.

## 3. Responsibility boundary: debounce vs cooldown

- Event Engine (Huy): suppresses noisy raw signal repetitions and decides event onset/offset before creating an event.
- Backend (Phúc): stores every valid event, emits `event.created`, and throttles only `alert.triggered` presentation messages.
- Frontend (Nam): renders the event timeline and alert messages.

**Cooldown never drops an event from PostgreSQL, the REST event list, or the `event.created` stream.** This prevents double debounce between Huy and Phúc.

## 4. Cooldown policy

- Default local/demo value: 15 seconds.
- Environment variable: `ALERT_COOLDOWN_SECONDS` (integer >= 0; `0` disables throttling).
- Key: `(session_id, event_type)`.
- `severity=INFO` does not produce `alert.triggered`.
- Cooldown starts from Backend `received_at`, not the client/source timestamp.
- This default is an implementation value for integration; final UX thresholds remain subject to group confirmation in T17/T25.

## 5. Session report

Existing endpoint remains `GET /api/v1/sessions/{session_id}/report`. It additionally returns:

- `counts_by_source`: counts by `AI_LEARNING`, `AI_EXAM`, `BROWSER`, `SYSTEM`.
- `alert_eligible_count`: events with severity other than INFO. This is **not** the number of notifications actually emitted after cooldown.
- `reviewed_count`: number of events marked reviewed.
- `first_event_at`, `last_event_at`: earliest/latest `occurred_at`, null when there are no events.

All values are computed from persisted rows in `events`; alert cooldown does not affect report totals.

## 6. Reconnect and deployment limits

- Live delivery is best-effort. The current MVP does not replay missed frames over WebSocket.
- After reconnect, client retrieves missed events through `GET /api/v1/sessions/{session_id}/events` with pagination/time filters.
- Connection registry and cooldown are in memory and require a single API worker. For multiple workers/containers, replace them with shared Redis Pub/Sub and shared cooldown state.
- Browser WebSocket uses a short-lived JWT query parameter for MVP convenience. Avoid logging full WebSocket URLs. A production deployment should use secure same-origin cookie authentication and validate Origin/CSRF policy.
