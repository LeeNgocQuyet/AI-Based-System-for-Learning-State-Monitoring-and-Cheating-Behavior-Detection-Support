# Backend Architecture & Contract v1.1 — Nhóm 3

**Đề tài:** Thiết kế và phát triển hệ thống giám sát trạng thái học tập và hỗ trợ phát hiện hành vi gian lận dựa trên trí tuệ nhân tạo.

**Trạng thái:** Final v1.1.0 — Đã hợp nhất toàn diện Auth, RBAC, Database Schema PostgreSQL và Event/Session Contract.

---

## 1. Cấu trúc thư mục Backend

Thư mục `backend/` được tổ chức theo chuẩn kiến trúc phần mềm phân tầng (Layered Architecture), đảm bảo tính module hóa và dễ bảo trì:

```
backend/
├── README.md                      # Tài liệu tổng quan kiến trúc và hướng dẫn vận hành v1.1.0
├── auth-rbac.md                   # Đặc tả chi tiết AuthN, AuthZ, ma trận phân quyền RBAC và test cases
├── event-ingest-v1.schema.json    # JSON Schema chuẩn cho sự kiện Browser/AI gửi lên Backend
├── event-record-v1.schema.json    # JSON Schema chuẩn cho sự kiện lưu trữ sau chuẩn hóa
├── openapi-v1.1.yaml              # OpenAPI 3.1.0 contract đầy đủ (Auth, Sessions, Events, Teacher, Report)
├── openapi-v1.yaml                # Alias đồng bộ cho OpenAPI contract
├── requirements-auth-seed.txt     # Thư viện phụ thuộc cho Database seed (psycopg, argon2-cffi)
├── database/
│   ├── schema-v1.sql              # PostgreSQL DDL hoàn chỉnh (Users, Sessions, Events, Grants, Tokens)
│   ├── seed_instructor.py         # Script khởi tạo tài khoản Giảng viên an toàn với Argon2id
│   ├── grant-instructor-session.sql # Script phân quyền phiên thi cho Giảng viên trong kịch bản demo
│   └── .env.example               # Mẫu cấu hình biến môi trường kết nối DB và JWT Secret
└── mocks/
    ├── auth-rbac-mock-payloads.json # Dữ liệu mock Auth, Login, Token, và các mã lỗi RBAC
    ├── event-mock-payloads.json   # Dữ liệu mock cho 10 loại Event, Session lifecycle và Report
    └── mock-payloads.json         # File mock hợp nhất tổng thể cho Frontend
```

---

## 2. Kiến trúc Bảo mật & Phân quyền (Auth & RBAC)

Hệ thống được thiết kế theo nguyên tắc **Zero Trust** đối với Client:
1. **Hai vai trò cốt lõi (`user_role`):** `LEARNER` (Người học) và `INSTRUCTOR` (Giảng viên).
2. **Đăng ký công khai (`POST /auth/register`):**
   - Chỉ tạo tài khoản với vai trò `LEARNER`.
   - Thuộc tính `additionalProperties: false` chặn mọi nỗ lực tự nâng quyền (`role: "INSTRUCTOR"` bị từ chối với lỗi `422`).
3. **Cấp phát Giảng viên (Instructor Provisioning):**
   - Giảng viên được cấp sẵn bằng script nội bộ `database/seed_instructor.py`. Không mở API public tạo Giảng viên.
4. **Cơ chế Token kép (Dual-Token Pattern):**
   - **Access Token:** JWT ngắn hạn (15 phút), lưu trong bộ nhớ client.
   - **Refresh Token:** Chuỗi ngẫu nhiên opaque token lưu trong cookie bảo mật `HttpOnly; Secure; SameSite=Lax`. Cơ sở dữ liệu chỉ lưu chuỗi hash SHA-256 (`refresh_tokens.token_hash`).
   - Mỗi lần refresh token (`POST /auth/refresh`), token cũ bị thu hồi ngay và xoay vòng (rotation) token mới.
5. **Kiểm tra quyền sở hữu dữ liệu (Backend-enforced Scope):**
   - **Người học:** Chỉ truy vấn các phiên có `sessions.learner_id = current_user_id`. Cố tình đọc session người khác sẽ nhận `404 Not Found` (không lộ sự tồn tại của session).
   - **Giảng viên:** Chỉ truy vấn các phiên có bản ghi phân quyền trong bảng allow-list `instructor_session_access`.
   - Tuyệt đối không dựa vào việc ẩn nút trên Frontend.

---

## 3. Quy chuẩn Vòng đời Phiên & Sự kiện (Session & Event Registry)

### 3.1. Vòng đời phiên (Session Lifecycle)
- **Chế độ học tập (`LEARNING`):** Cho phép `ACTIVE` $\leftrightarrow$ `PAUSED` $\rightarrow$ `ENDED`.
- **Chế độ thi (`EXAM`):** **Nghiêm cấm `PAUSED`** (được ràng buộc ở cả database constraint `ck_sessions_exam_no_pause` lẫn tầng API validation trả về `400 EXAM_PAUSE_NOT_ALLOWED`).
- **Thời lượng (`duration_ms`):** Tính toán chính xác từ các khoảng thời gian `ACTIVE`; toàn bộ thời gian `PAUSED` bị loại trừ.

### 3.2. Danh mục 10 mã sự kiện chuẩn hóa
| `event_type` | `source` hợp lệ | Module chịu trách nhiệm | Ý nghĩa hiển thị trung tính |
|---|---|---|---|
| `EYES_CLOSED_LONG` | `AI_LEARNING` | Quyết (AI Học tập) | Hệ thống ghi nhận dấu hiệu nhắm mắt kéo dài. |
| `YAWN_DETECTED` | `AI_LEARNING` | Quyết (AI Học tập) | Hệ thống ghi nhận dấu hiệu ngáp. |
| `HEAD_NOD_DETECTED` | `AI_LEARNING` | Quyết (AI Học tập) | Hệ thống ghi nhận chuyển động gật đầu lặp lại. |
| `LOOK_AWAY_DETECTED` | `AI_LEARNING` / `AI_EXAM` | Quyết / Huy | Hệ thống ghi nhận hướng nhìn/đầu lệch khỏi vùng quan sát. |
| `FACE_NOT_DETECTED` | `AI_LEARNING` / `AI_EXAM` | Quyết / Huy | Không phát hiện được khuôn mặt trong khung hình. |
| `MULTIPLE_FACES_DETECTED` | `AI_EXAM` | Huy (AI Giám sát thi) | Phát hiện nhiều hơn một khuôn mặt trong khung hình. |
| `PHONE_DETECTED` | `AI_EXAM` | Huy (AI Giám sát thi) | Mô hình phát hiện vật thể nghi vấn là điện thoại (thực nghiệm). |
| `TAB_HIDDEN` | `BROWSER` | Nam (Frontend) | Trang kiểm tra chuyển sang trạng thái không hiển thị. |
| `CAMERA_LOST` | `BROWSER` | Nam (Frontend) | Tín hiệu webcam bị gián đoạn. |
| `CONNECTION_LOST` | `SYSTEM` | Phúc (Backend) | Kết nối truyền dữ liệu tới máy chủ bị gián đoạn. |

- **Nguyên tắc đạo đức (HCI):** Backend gán mức `severity` (`INFO`, `LOW`, `MEDIUM`, `HIGH`) và thông điệp trung tính; không đưa ra kết luận "gian lận".
- **Duyệt sự kiện (S11):** Giảng viên có thể cập nhật trạng thái `is_reviewed: true` qua `PATCH /sessions/{id}/events/{event_id}/review`.

---

## 4. Danh mục REST API

Base URL local: `http://localhost:8000/api/v1`

| Nhóm | Method | Endpoint | Quyền hạn | Mục đích |
|---|---|---|---|---|
| **Auth** | `POST` | `/auth/register` | Public | Đăng ký tài khoản Người học (S02) |
| | `POST` | `/auth/login` | Public | Đăng nhập, cấp Access JWT + Refresh Cookie (S01) |
| | `GET` | `/auth/me` | Bearer Auth | Lấy hồ sơ tài khoản và vai trò (`role`) hiện tại |
| | `POST` | `/auth/refresh` | Refresh Cookie | Cấp lại access token và xoay vòng refresh cookie |
| | `POST` | `/auth/logout` | Bearer + Cookie | Thu hồi refresh token và xóa cookie |
| **Sessions** | `POST` | `/sessions` | Learner | Tạo phiên mới (`LEARNING` hoặc `EXAM`) |
| | `GET` | `/sessions/mine` | Learner | Lấy danh sách phiên của chính mình (S04, S09) |
| | `GET` | `/sessions/{id}` | Chủ phiên / Instructor | Xem chi tiết phiên |
| | `PATCH` | `/sessions/{id}/status` | Chủ phiên | Tạm dừng/tiếp tục/kết thúc (Chặn PAUSE nếu thi) |
| | `GET` | `/sessions/{id}/report` | Chủ phiên / Instructor | Lấy báo cáo thống kê tổng hợp phiên |
| **Events** | `POST` | `/sessions/{id}/events` | Chủ phiên / AI Service | Đẩy sự kiện vào Backend (chống trùng lặp qua `event_id`) |
| | `GET` | `/sessions/{id}/events` | Chủ phiên / Instructor | Lấy danh sách sự kiện theo bộ lọc |
| **Teacher** | `GET` | `/teacher/sessions` | Instructor | Dashboard phiên có grant, hỗ trợ query `search` (S10) |
| | `PATCH` | `/sessions/{id}/events/{event_id}/review` | Instructor | Đánh dấu sự kiện đã xem xét (S11) |

---

## 5. Quy chuẩn WebSocket cho Cảnh báo Thời gian thực

1. **Kênh Người học (`ws://localhost:8000/api/v1/ws/sessions/{session_id}?token={JWT}`):**
   - Backend đẩy thông điệp nhắc nhở trung tính xuống giao diện học tập S06/S08 khi phát hiện dấu hiệu buồn ngủ hoặc mất tập trung.
2. **Kênh Giảng viên (`ws://localhost:8000/api/v1/ws/teacher/live?token={JWT}`):**
   - Backend đẩy các sự kiện `MEDIUM` hoặc `HIGH` trong phòng thi tới Dashboard S10/S11 theo thời gian thực.

---

## 6. Hướng dẫn Khởi chạy Database & Seed dữ liệu Local

### Bước 1: Khởi tạo CSDL PostgreSQL 15+
```bash
# Tạo database
createdb -U postgres learning_monitor

# Áp dụng schema DDL
psql -U postgres -d learning_monitor -f database/schema-v1.sql
```

### Bước 2: Cài đặt thư viện Seed
```bash
pip install -r requirements-auth-seed.txt
```

### Bước 3: Khởi tạo tài khoản Giảng viên (Seed Instructor)
```bash
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/learning_monitor"
export INSTRUCTOR_EMAIL="instructor.demo@university.edu.vn"
export INSTRUCTOR_FULL_NAME="TS. Trần Giảng Viên"
export INSTRUCTOR_PASSWORD="DemoSecurePassword123!"

python database/seed_instructor.py
```

### Bước 4: Cấp quyền xem phiên cho Giảng viên (Grant Session)
Khi sinh viên tạo phiên demo có ID cụ thể, chạy script sau để cấp quyền cho Giảng viên:
```bash
psql "$DATABASE_URL" \
  -v instructor_email='instructor.demo@university.edu.vn' \
  -v session_id='ab67e8c2-9cc0-4b3c-8e1d-fc944b7c9102' \
  -f database/grant-instructor-session.sql
```
