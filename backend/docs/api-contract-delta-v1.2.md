# API Contract Delta v1.2

Bản này kế thừa `openapi-v1.1-reference.yaml`, giữ nguyên `/api/v1` và event schema `1.0.0`.

## Endpoint Session lifecycle thực thi

| Method | Path | Kết quả |
|---|---|---|
| POST | `/api/v1/sessions` | Tạo session với status `ACTIVE`; tạo = start |
| PATCH | `/api/v1/sessions/{session_id}/status` | Pause, resume hoặc end bằng status body |
| POST | `/api/v1/sessions/{session_id}/start` | Resume session đang pause; tiện dụng cho UI |
| POST | `/api/v1/sessions/{session_id}/end` | End session; tiện dụng cho UI |

`POST /start` và `POST /end` là convenience routes. Client vẫn có thể dùng PATCH `/status` theo contract v1.1.

## Endpoint Event

`POST /api/v1/sessions/{session_id}/events` nhận đúng một payload Event Ingest v1.0.0 mỗi request.

- `201`: event mới được lưu.
- `200`: retry có cùng `event_id` và payload giống hệt, sau khi caller được xác thực quyền.
- `400`: body `session_id` khác path `session_id`.
- `403`: user/service token không được phép phát source đó hoặc service source không khớp loại session.
- `404`: session không tồn tại hoặc caller không có quyền với session.
- `409`: session không active hoặc `event_id` đã tồn tại với payload khác.
- `422`: payload sai schema/quy ước timestamp/source.

`GET /api/v1/sessions/{session_id}/events` hỗ trợ lọc `event_type`, `severity`, `source`, `from`, `to`, `page`, `page_size`.

## Bảo mật & toàn vẹn

- Learner owner được xác định từ principal đã xác thực; không nhận owner ID từ body.
- Instructor được đọc session/event/report khi có bản ghi trong `instructor_session_access`.
- Service token không được đọc session và không được gửi `BROWSER` event.
- User token chỉ được gửi `BROWSER` event cho session thuộc chính user.
- Backend gán `received_at`, `severity`, `message`.
- Kiểm tra quyền với target session trước khi giải quyết idempotency bằng `event_id`, không trả event cũ trước bước authorization.
- `AI_LEARNING` chỉ gửi vào session `LEARNING`; `AI_EXAM` chỉ gửi vào session `EXAM`.

## Severity policy

Ngưỡng v1.2 được định nghĩa tại README để phục vụ mock và API integration. Nhóm AI cần xác nhận trước khi đóng băng contract; severity không được hiểu là kết luận hành vi gian lận.

`PHONE_DETECTED` là event thử nghiệm và API từ chối mặc định. Chỉ bật qua `ENABLE_PHONE_DETECTION=true` sau khi nhóm AI xác nhận mô hình ổn định.
