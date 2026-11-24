# Backend Security, Reliability & Performance Validation — v1.4

## 1. Mục tiêu kiểm thử

| Nhóm | Mục tiêu | Tiêu chí PASS |
|---|---|---|
| **Auth/RBAC** | Learner A không đọc session/event/report của Learner B | 404 trên mọi endpoint |
| **Auth/RBAC** | Instructor chỉ đọc session có grant | 404 khi chưa có grant |
| **Auth/RBAC** | Request không có token bị từ chối | 401 |
| **WebSocket** | Token thiếu/sai hoặc role sai bị từ chối | `WebSocketDisconnect` |
| **WebSocket** | Learner B không subscribe session của A | `WebSocketDisconnect` |
| **Reliability** | Sau disconnect: registry sạch, log có connected/disconnected | Không còn subscriber |
| **Reliability** | JWT không bị ghi vào log | `token not in caplog.text` |
| **Reliability** | Ping/Pong hoạt động đúng | `{"type":"pong"}` |
| **Performance** | Latency mean/P95/P99, throughput, error rate | Ghi số đo thật |

---

## 2. Chạy Unit Tests (SQLite in-memory)

```bash
# Từ thư mục backend/
pip install -r requirements-dev.txt
pytest -q
# Hoặc chỉ chạy test mới:
pytest tests/test_security_reliability.py -v
```

Bộ test gồm **14 test cases** trong `tests/test_security_reliability.py`:

| Test | Mô tả |
|---|---|
| `TestLearnerIsolation::test_learner_b_cannot_read_a_session` | B không đọc session của A |
| `TestLearnerIsolation::test_learner_b_cannot_read_a_events` | B không đọc events của A |
| `TestLearnerIsolation::test_learner_b_cannot_read_a_report` | B không đọc report của A |
| `TestLearnerIsolation::test_learner_b_cannot_read_a_session_events_or_report` | Kiểm tra đồng thời 3 endpoint |
| `TestInstructorIsolation::test_instructor_without_grant_cannot_read_session` | Instructor không có grant → 404 |
| `TestInstructorIsolation::test_instructor_without_grant_cannot_read_events` | Instructor không có grant → 404 |
| `TestInstructorIsolation::test_instructor_without_grant_cannot_read_report` | Instructor không có grant → 404 |
| `TestUnauthenticated::test_no_token_sessions_mine` | Không có token → 401 |
| `TestUnauthenticated::test_no_token_create_session` | Không có token → 401 |
| `TestUnauthenticated::test_invalid_token_returns_401` | Token sai → 401 |
| `TestWebSocketAuth::test_rejects_missing_and_invalid_token` | WS bị từ chối khi thiếu/sai token |
| `TestWebSocketAuth::test_rejects_wrong_role_instructor_on_learner_channel` | Instructor không dùng kênh learner |
| `TestWebSocketAuth::test_rejects_learner_on_teacher_channel` | Learner không dùng kênh teacher |
| `TestWebSocketAuth::test_rejects_learner_b_on_session_owned_by_a` | B không subscribe session của A |
| `TestWebSocketReliability::test_disconnect_cleans_registry_and_logs` | Registry sạch + log đúng + JWT không lộ |
| `TestWebSocketReliability::test_ping_pong` | Ping/Pong hoạt động |
| `TestWebSocketReliability::test_teacher_websocket_connect_and_disconnect` | Teacher WS lifecycle |
| `TestWebSocketReliability::test_rejected_ws_logs_warning` | Từ chối → ghi warning log |

---

## 3. Log kết nối WebSocket

`app/api/v1/websocket.py` ghi log theo chuẩn structured key=value qua `logging.getLogger(__name__)`:

| Sự kiện | Level | Format ví dụ |
|---|---|---|
| Kết nối thành công (learner) | INFO | `websocket.connected channel=session session_id=<uuid> user_id=<uuid>` |
| Kết nối thành công (teacher) | INFO | `websocket.connected channel=teacher user_id=<uuid>` |
| Ngắt kết nối (learner) | INFO | `websocket.disconnected channel=session session_id=<uuid> user_id=<uuid>` |
| Ngắt kết nối (teacher) | INFO | `websocket.disconnected channel=teacher user_id=<uuid>` |
| Từ chối — thiếu token | WARNING | `websocket.rejected channel=session session_id=<uuid> reason=missing_token` |
| Từ chối — token sai | WARNING | `websocket.rejected channel=session session_id=<uuid> reason=invalid_token` |
| Từ chối — role sai | WARNING | `websocket.rejected channel=session session_id=<uuid> reason=role_denied` |
| Từ chối — ngoài phạm vi | WARNING | `websocket.rejected channel=session session_id=<uuid> user_id=<uuid> reason=scope_denied` |

> [!IMPORTANT]
> JWT token **không bao giờ được ghi vào log**. Chỉ ghi `user_id` (UUID). Test `test_disconnect_cleans_registry_and_logs` xác minh điều này tự động.

---

## 4. Reconnect Strategy (Frontend)

```
1. Kết nối /api/v1/ws/sessions/{session_id}?token=...
2. Nhận {"type":"connection.ready", "replay_available":false}
3. Khi socket đóng → Backend log websocket.disconnected và xóa khỏi registry
4. Frontend reconnect theo exponential backoff: 1s → 2s → 4s → 8s → 30s (max)
5. Nhận connection.ready → gọi GET /api/v1/sessions/{id}/events để bù dữ liệu bị bỏ lỡ
```

> [!NOTE]
> PostgreSQL là nguồn dữ liệu bền vững. WebSocket chỉ là live delivery. Reconnect + REST catch-up đảm bảo không mất event.

---

## 5. Chạy Benchmark Hiệu năng

### Yêu cầu
```bash
pip install httpx psutil   # psutil: đo CPU/RAM client process
```

### Phát token & chạy benchmark
```bash
# Bước 1: Phát learner token
python scripts/issue_user_token.py --email learner.one@example.edu

# Bước 2: Chạy API server (một cửa sổ riêng)
uvicorn app.main:app --port 8000

# Bước 3: Chạy benchmark (10 session đồng thời, 5 round)
python scripts/benchmark_api.py \
    --token "<PASTE_TOKEN_HERE>" \
    --concurrent-sessions 10 \
    --rounds 5 \
    --output-dir benchmark-results
```

### Mỗi round thực hiện đồng thời (per session):
1. `POST /api/v1/sessions/{id}/events` — event ingest
2. `GET /api/v1/sessions/{id}/events?page=1&page_size=100` — event list
3. `GET /api/v1/sessions/{id}/report` — session report

**Kết quả:** `benchmark-results/backend_benchmark_report.json` và `backend_benchmark_samples.csv`

---

## 6. Đo Resource Server (Docker)

```bash
# Lấy CPU/RAM của container API (không phải client process)
docker stats --no-stream

# Hoặc giám sát liên tục khi benchmark đang chạy
docker stats
```

> [!WARNING]
> `psutil` trong `benchmark_api.py` chỉ đo CPU/RSS của **tiến trình benchmark client**, không phải server. Phải dùng `docker stats` hoặc hệ thống monitoring riêng để đo resource phía server.

---

## 7. Bảng nghiệm thu — điền bằng số đo thật

| Thuộc tính | Kết quả |
|---|---|
| **Máy chạy Backend / OS** | Chưa đo |
| **CPU / cores** | Chưa đo |
| **RAM** | Chưa đo |
| **Python version** | Chưa đo |
| **PostgreSQL version** | Chưa đo |
| **Docker version** | Chưa đo |
| **Uvicorn workers** | 1 (MVP default) |
| **Concurrent sessions đo** | Chưa đo |
| **Total requests / error rate** | Chưa đo |
| **Latency mean** | Chưa đo |
| **Latency P95** | Chưa đo |
| **Latency P99** | Chưa đo |
| **Throughput (req/s)** | Chưa đo |
| **CPU server (docker stats)** | Chưa đo |
| **RAM server (docker stats)** | Chưa đo |
| **AI FPS** | Đo riêng bởi AI Core |

> [!CAUTION]
> **Không đánh dấu PASS hiệu năng** trước khi chạy benchmark trên máy đích thực tế và lưu file JSON/CSV kết quả.

---

## 8. Giới hạn MVP

- WebSocket manager chạy **in-memory** một Uvicorn worker; không scale ngang.
- Khi scale nhiều worker/container → cần **Redis Pub/Sub** hoặc message broker dùng chung.
- Cooldown `alert.triggered` cũng in-memory — reset khi restart server.
- Event luôn bền vững trong PostgreSQL; chỉ live delivery mới có thể bị mất khi mất kết nối.
