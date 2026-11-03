# Backend Contract v1 — Nhóm 3

**Đề tài:** Thiết kế và phát triển hệ thống giám sát trạng thái học tập và hỗ trợ phát hiện hành vi gian lận dựa trên trí tuệ nhân tạo.

**Trạng thái:** Final Draft v1.0.0 — Đã cập nhật và đồng bộ 100% theo tài liệu Báo cáo tiến độ và Đặc tả UI/UX.

---

## 1. Phạm vi tài liệu & Cấu trúc thư mục

Bộ hợp đồng này chuẩn hóa toàn bộ giao tiếp giữa Frontend (Nam), hai module AI (Quyết & Huy) và Backend (Phúc):

- `event-ingest-v1.schema.json`: JSON Schema chuẩn để Frontend/AI gửi sự kiện vào Backend.
- `event-record-v1.schema.json`: JSON Schema chuẩn của sự kiện sau khi Backend xác thực, chuẩn hóa severity, gán nhãn trung tính và lưu trữ.
- `openapi-v1.yaml`: Đặc tả OpenAPI 3.1.0 đầy đủ cho toàn bộ REST API (Auth, Sessions, Events, Teacher Dashboard, Report).
- `mock-payloads.json`: Dữ liệu mẫu hoàn chỉnh (Auth, Session, 10 Event types, Report, Error codes) phục vụ Frontend và AI mock test độc lập.

---

## 2. Các quy ước bắt buộc (Chốt toàn nhóm)

| Trường dữ liệu | Quy ước kỹ thuật | Ghi chú tích hợp |
|---|---|---|
| `event_id` | UUID v4 do producer tự sinh khi phát hiện sự kiện. | Dùng để chống ghi trùng (Idempotency). Khi retry do lỗi mạng, **phải giữ nguyên `event_id` cũ**. |
| `session_id` | UUID v4 do Backend cấp khi tạo phiên. | Mọi sự kiện phát ra bắt buộc phải gắn với `session_id` này. |
| `schema_version` | Cố định chuỗi `"1.0.0"`. | Đảm bảo tương thích ngược. |
| `occurred_at` | RFC 3339 / ISO 8601 UTC có đuôi `Z` (ví dụ `2026-11-02T06:35:12.345Z`). | Thời điểm sự kiện thực tế xảy ra. Frontend dùng `new Date().toISOString()`. |
| `received_at` | Backend tự sinh khi lưu trữ. | Producer **không gửi** trường này. |
| `source` | Chỉ dùng: `AI_LEARNING`, `AI_EXAM`, `BROWSER`, `SYSTEM`. | Không điền tên model, tên thư viện hay chuỗi tự do. |
| `duration_ms` | Millisecond của chính dấu hiệu/sự kiện đó. | Bỏ qua nếu là sự kiện tức thời hoặc chưa tính được thời lượng. |
| `confidence` | Số thực trong `[0.0, 1.0]`. | Chỉ gửi từ module AI; Frontend/Browser không gửi trường này. |
| `severity` | Backend chuẩn hóa: `INFO`, `LOW`, `MEDIUM`, `HIGH`. | AI/Frontend **không tự quyết định**. Đây không phải kết luận gian lận. |
| `is_reviewed` | Boolean (`false` mặc định). | Dành cho Giảng viên đánh dấu đã xem lại sự kiện (S11). |
| `metadata` | Object chứa chi tiết kỹ thuật riêng biệt. | **Tuyệt đối không gửi ảnh base64, video frame hay thông tin nhạy cảm**. |

---

## 3. Danh mục 10 mã sự kiện chuẩn hóa (Event Registry)

| `event_type` | Thông điệp hiển thị trung tính (Message) | `source` hợp lệ | Module chịu trách nhiệm |
|---|---|---|---|
| `EYES_CLOSED_LONG` | Hệ thống ghi nhận dấu hiệu nhắm mắt kéo dài. | `AI_LEARNING` | Quyết (AI Học tập) |
| `YAWN_DETECTED` | Hệ thống ghi nhận dấu hiệu ngáp. | `AI_LEARNING` | Quyết (AI Học tập) |
| `HEAD_NOD_DETECTED` | Hệ thống ghi nhận chuyển động gật đầu lặp lại. | `AI_LEARNING` | Quyết (AI Học tập) |
| `LOOK_AWAY_DETECTED` | Hệ thống ghi nhận hướng nhìn/đầu lệch khỏi vùng quan sát. | `AI_LEARNING` hoặc `AI_EXAM` | Quyết / Huy |
| `FACE_NOT_DETECTED` | Không phát hiện được khuôn mặt trong khung hình. | `AI_LEARNING` hoặc `AI_EXAM` | Quyết / Huy |
| `MULTIPLE_FACES_DETECTED` | Phát hiện nhiều hơn một khuôn mặt trong khung hình. | `AI_EXAM` | Huy (AI Giám sát thi) |
| `PHONE_DETECTED` | Mô hình phát hiện vật thể nghi vấn là điện thoại. | `AI_EXAM` | Huy (AI Thi - Thực nghiệm/Optional) |
| `TAB_HIDDEN` | Trang kiểm tra chuyển sang trạng thái không hiển thị. | `BROWSER` | Nam (Frontend - Visibility API) |
| `CAMERA_LOST` | Tín hiệu webcam bị gián đoạn. | `BROWSER` | Nam (Frontend - MediaStream) |
| `CONNECTION_LOST` | Kết nối truyền dữ liệu tới máy chủ bị gián đoạn. | `SYSTEM` | Phúc (Backend / Heartbeat) |

> [!NOTE]
> **Quy ước sự kiện rời Tab (`TAB_HIDDEN`):**
> Khi sinh viên rời tab kiểm tra, Frontend bắt sự kiện `document.visibilitychange`. Khi sinh viên quay lại tab, Frontend tính khoảng thời gian rời tab (`duration_ms = returnTime - leaveTime`) và gửi 1 bản ghi `TAB_HIDDEN` kèm `duration_ms`. Nếu sinh viên không quay lại trước khi hết giờ, sự kiện được gửi với `duration_ms: null`.

---

## 4. Danh sách REST API Contract

Base URL local: `http://localhost:8000/api/v1`

### 4.1. Xác thực & Tài khoản (S01, S02)
- `POST /auth/register`: Đăng ký tài khoản Người học (Màn hình S02). Hệ thống mặc định gán role `LEARNER`. Không mở đăng ký vai trò Giảng viên.
- `POST /auth/login`: Đăng nhập chung (S01). Trả về JWT Access Token cùng thông tin user và vai trò (`LEARNER` hoặc `TEACHER`) để Frontend điều hướng (Learner $\rightarrow$ S04; Teacher $\rightarrow$ S10).
- `GET /auth/me`: Lấy thông tin tài khoản đang đăng nhập.

### 4.2. Quản lý Phiên (Sessions - S04, S06, S08, S09)
- `POST /sessions`: Người học tạo phiên mới (`session_type: "LEARNING"` hoặc `"EXAM"`).
- `GET /sessions/mine`: Người học lấy danh sách lịch sử phiên của chính mình.
- `GET /sessions/{session_id}`: Lấy chi tiết phiên (Chủ phiên hoặc Giảng viên phụ trách).
- `PATCH /sessions/{session_id}/status`: Cập nhật trạng thái phiên:
  - Phiên `LEARNING`: Cho phép `ACTIVE` $\leftrightarrow$ `PAUSED` $\rightarrow$ `ENDED`.
  - Phiên `EXAM`: **Nghiêm cấm `PAUSED`** (trả về lỗi `400 EXAM_PAUSE_NOT_ALLOWED`), chỉ cho phép `ACTIVE` $\rightarrow$ `ENDED`.
- `GET /sessions/{session_id}/report`: Lấy báo cáo thống kê tổng hợp của phiên.

### 4.3. Quản lý Sự kiện (Events - S06, S08, S11)
- `POST /sessions/{session_id}/events`: Đẩy sự kiện vào Backend (hỗ trợ Idempotent retry qua `event_id`).
- `GET /sessions/{session_id}/events`: Lấy danh sách sự kiện theo bộ lọc (`event_type`, `severity`, `source`, `is_reviewed`, `from`, `to`).

### 4.4. Giảng viên (Teacher Dashboard - S10, S11, S12)
- `GET /teacher/sessions`: Giảng viên xem danh sách các phiên thuộc phạm vi quản lý. Hỗ trợ lọc theo `status`, `session_type`, `event_severity`, và tìm kiếm từ khóa qua `search` (tên/mã người học).
- `PATCH /sessions/{session_id}/events/{event_id}/review`: Giảng viên đánh dấu đã xem xét sự kiện (`is_reviewed: true`).

---

## 5. Quy chuẩn WebSocket cho Cảnh báo Thời gian thực (Real-time)

Nhằm đảm bảo phản hồi tức thì mà không cần polling liên tục:

1. **Kênh Người học (Learner WebSocket):**
   - URL: `ws://localhost:8000/api/v1/ws/sessions/{session_id}?token={JWT}`
   - Chiều dữ liệu: Backend $\rightarrow$ Frontend.
   - Nội dung: Đẩy các cảnh báo nhắc nhở trung tính khi Backend phát hiện dấu hiệu bất thường (ví dụ: nhắm mắt lâu, mất khuôn mặt).
2. **Kênh Giảng viên (Teacher Live WebSocket):**
   - URL: `ws://localhost:8000/api/v1/ws/teacher/live?token={JWT}`
   - Chiều dữ liệu: Backend $\rightarrow$ Frontend.
   - Nội dung: Đẩy các sự kiện có mức độ `MEDIUM` hoặc `HIGH` trong phòng thi để Giảng viên theo dõi ngay trên Dashboard S10/S11.

---

## 6. Xử lý lỗi chuẩn mực (Mục 11 Đặc tả)

Mọi phản hồi lỗi từ API đều tuân thủ cấu trúc chuẩn:
```json
{
  "error": {
    "code": "MÃ_LỖI",
    "message": "Thông điệp thân thiện, không tiết lộ thông tin nhạy cảm",
    "details": {}
  }
}
```
Các mã lỗi chính:
- `400 EXAM_PAUSE_NOT_ALLOWED`: Chế độ thi không cho phép tạm dừng.
- `401 INVALID_CREDENTIALS`: Sai tài khoản/mật khẩu (không nói rõ tài khoản có tồn tại hay không).
- `403 INSUFFICIENT_PERMISSIONS`: Không đủ quyền truy cập (Người học cố tình gọi API Giảng viên).
- `404 SESSION_NOT_FOUND`: Không tìm thấy phiên hoặc phiên không thuộc quyền xem.
- `409 SESSION_ALREADY_ENDED`: Không thể gửi event vào phiên đã đóng.
- `422 VALIDATION_FAILED`: Dữ liệu không khớp schema.
