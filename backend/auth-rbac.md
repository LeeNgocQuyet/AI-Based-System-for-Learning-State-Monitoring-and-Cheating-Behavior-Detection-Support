# Auth, RBAC & Database — Nhóm 3 (Draft v1.1.0)

## 1. Phạm vi kiến trúc

Tài liệu này bổ sung Authentication, Authorization (RBAC) và schema PostgreSQL vào event/session contract v1. Phạm vi bám sát theo đặc tả UI/UX:
- Hai vai trò cốt lõi: `LEARNER` (Người học) và `INSTRUCTOR` (Giảng viên).
- Đăng ký công khai (`POST /auth/register`) chỉ tạo Người học (`LEARNER`).
- Giảng viên (`INSTRUCTOR`) được nhóm cấp sẵn qua provisioning script; không mở API tự đăng ký quyền giảng viên.
- Phân quyền thực sự ở tầng Backend; không dựa vào việc ẩn nút trên giao diện frontend.
- Người học chỉ có quyền xem phiên/sự kiện do chính mình sở hữu.
- Giảng viên chỉ có quyền xem các phiên đã được phân quyền trong bảng `instructor_session_access`.

---

## 2. Quy ước tài khoản (Users)

| Trường | Kiểu dữ liệu | Quy ước kỹ thuật |
|---|---|---|
| `user_id` | UUID | Khóa chính tự sinh (`gen_random_uuid()`). |
| `email` | VARCHAR(320) | Bắt buộc, chuẩn hóa lowercase, duy nhất (`UQ`). |
| `full_name` | VARCHAR(120) | Bắt buộc, không để trống (`CHECK (LENGTH(TRIM(full_name)) > 0)`). |
| `password_hash` | TEXT | Mã hóa bằng **Argon2id**; tuyệt đối không lưu mật khẩu thuần. |
| `role` | `user_role` ENUM | Chỉ nhận `'LEARNER'` hoặc `'INSTRUCTOR'`. Role luôn lấy từ database, không tin role client gửi. |
| `status` | `account_status` ENUM | `'ACTIVE'` hoặc `'DISABLED'`. |
| `created_at`, `updated_at` | TIMESTAMPTZ | Lưu múi giờ UTC, tự cập nhật qua database trigger. |

---

## 3. Auth API Contract

Base URL: `http://localhost:8000/api/v1`

| Method | Endpoint | Xác thực | Mục đích |
|---|---|---|---|
| `POST` | `/auth/register` | Public | Tạo tài khoản `LEARNER`; request không chứa trường `role` |
| `POST` | `/auth/login` | Public | Xác thực email/password, cấp short-lived access token và HttpOnly refresh token cookie |
| `GET` | `/auth/me` | Bearer Token | Lấy hồ sơ tài khoản và vai trò (`role`) hiện tại |
| `POST` | `/auth/refresh` | Refresh Cookie | Xoay vòng (rotate) refresh token, cấp access token mới |
| `POST` | `/auth/logout` | Bearer + Cookie | Thu hồi refresh token trong DB, xóa cookie phía trình duyệt |

### 3.1. Đăng ký (Register — S02)
- Endpoint: `POST /api/v1/auth/register`
- Schema yêu cầu `additionalProperties: false`.
- Request body chỉ nhận: `full_name`, `email`, `password`.
- Bất kỳ request nào gửi kèm `role: "INSTRUCTOR"` hoặc cố tình gán role đều bị từ chối với mã lỗi `422 Unprocessable Entity` (không âm thầm nhận hoặc tự nâng quyền).

### 3.2. Đăng nhập (Login — S01)
- Endpoint: `POST /api/v1/auth/login`
- Trả về short-lived JWT access token (thời hạn 15 phút) trong JSON body.
- Đồng thời đặt refresh token ngẫu nhiên trong cookie bảo mật:
  `Set-Cookie: refresh_token=<opaque-token>; HttpOnly; Secure; SameSite=Lax; Path=/api/v1/auth; Max-Age=604800`
- Cơ sở dữ liệu chỉ lưu chuỗi hash SHA-256 của refresh token (`refresh_tokens.token_hash`), không lưu token thuần.
- Nếu sai email hoặc mật khẩu, trả về thông điệp lỗi chung: `"Thông tin đăng nhập chưa đúng."` để tránh tấn công dò quét tài khoản (Username Enumeration).

---

## 4. Provisioning tài khoản Giảng viên

- Không có màn hình hoặc API công khai để tạo tài khoản Giảng viên trong phiên bản demo MVP.
- Nhóm chạy script `database/seed_instructor.py` thông qua biến môi trường bảo mật:
  ```bash
  export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/learning_monitor'
  export INSTRUCTOR_EMAIL='instructor.demo@university.edu.vn'
  export INSTRUCTOR_FULL_NAME='TS. Trần Giảng Viên'
  export INSTRUCTOR_PASSWORD='PrivatePassword123!'
  python database/seed_instructor.py
  ```
- Script tự động băm mật khẩu bằng Argon2id. Nếu email đã thuộc tài khoản `LEARNER`, script sẽ dừng và từ chối nâng quyền để đảm bảo an toàn.

---

## 5. Ma trận phân quyền (RBAC Permission Matrix)

| API / Thao tác | LEARNER | INSTRUCTOR | AI Module (Service Token) |
|---|:---:|:---:|:---:|
| `POST /auth/register` | ✅ (Tạo Learner) | ❌ | ❌ |
| `POST /auth/login` | ✅ | ✅ | ❌ |
| `GET /auth/me` | ✅ (Profile của mình) | ✅ (Profile của mình) | ❌ |
| `POST /sessions` | ✅ (Tạo phiên của mình) | ❌ (`403 Forbidden`) | ❌ |
| `GET /sessions/mine` | ✅ (Chỉ phiên của mình) | ❌ (`403 Forbidden`) | ❌ |
| `GET /sessions/{id}` | ✅ (Chỉ phiên mình sở hữu) | ✅ (Chỉ phiên có grant) | ❌ |
| `PATCH /sessions/{id}/status` | ✅ (Chủ phiên; cấm PAUSE nếu EXAM) | ❌ (`403 Forbidden`) | ❌ |
| `POST /sessions/{id}/events` | ✅ (Chỉ gửi `source: BROWSER`) | ❌ (`403 Forbidden`) | ✅ (Phát đúng `source` AI được cấp) |
| `GET /sessions/{id}/events` | ✅ (Phiên của mình) | ✅ (Phiên có grant) | ❌ |
| `PATCH /sessions/{id}/events/{event_id}/review` | ❌ (`403 Forbidden`) | ✅ (Phiên có grant) | ❌ |
| `GET /sessions/{id}/report` | ✅ (Tóm tắt cá nhân) | ✅ (Báo cáo phiên có grant) | ❌ |
| `GET /teacher/sessions` | ❌ (`403 Forbidden`) | ✅ (Chỉ các phiên có grant) | ❌ |

---

## 6. Mẫu truy vấn kiểm tra quyền bắt buộc (Security Query Patterns)

### 6.1. Người học (Learner Scope):
Mọi truy vấn dữ liệu phiên và sự kiện từ tài khoản Người học bắt buộc phải ràng buộc theo `learner_id`:
```sql
SELECT s.*
FROM sessions AS s
WHERE s.session_id = :session_id
  AND s.learner_id = :current_user_id;
```

### 6.2. Giảng viên (Instructor Grant Scope):
Giảng viên chỉ được xem các phiên nằm trong danh sách phân quyền allow-list `instructor_session_access`:
```sql
SELECT s.*
FROM sessions AS s
JOIN instructor_session_access AS a
  ON a.session_id = s.session_id
JOIN users AS instructor
  ON instructor.user_id = a.instructor_id
WHERE s.session_id = :session_id
  AND a.instructor_id = :current_user_id
  AND instructor.role = 'INSTRUCTOR'
  AND instructor.status = 'ACTIVE';
```

> [!IMPORTANT]
> **Quy tắc bảo mật phản hồi 404 vs 403:**
> - Nếu người dùng truy cập vào tài nguyên (phiên/sự kiện) không thuộc phạm vi của mình, Backend phải trả về `404 Not Found` (để tránh rò rỉ thông tin về sự tồn tại của phiên).
> - Nếu người dùng đúng danh tính nhưng gọi nhầm endpoint dành riêng cho role khác (ví dụ Learner gọi `/teacher/sessions`), Backend trả về `403 Forbidden`.

---

## 7. Kiểm soát vòng đời phiên & Thời lượng chính xác

- **Bắt đầu phiên (`POST /sessions`):**
  Trạng thái `ACTIVE`, `started_at = NOW()`, `active_started_at = NOW()`, `accumulated_active_ms = 0`.
- **Tạm dừng (`PATCH /status -> PAUSED`):**
  - **Chỉ áp dụng cho `LEARNING`**: Ràng buộc database `ck_sessions_exam_no_pause` và validation tầng API cấm chuyển sang `PAUSED` nếu `session_type == 'EXAM'`.
  - Cộng `NOW() - active_started_at` vào `accumulated_active_ms`.
  - Đặt `active_started_at = NULL`, `paused_at = NOW()`, `status = 'PAUSED'`.
- **Tiếp tục (`PATCH /status -> ACTIVE`):**
  Đặt `active_started_at = NOW()`, `paused_at = NULL`, `status = 'ACTIVE'`.
- **Kết thúc (`PATCH /status -> ENDED`):**
  Nếu đang `ACTIVE`, cộng nốt khoảng thời gian từ `active_started_at` đến `NOW()`. Đặt `ended_at = NOW()`, `status = 'ENDED'`.
- **Thời lượng `duration_ms`:** Luôn loại trừ toàn bộ thời gian `PAUSED`, chỉ tính thời gian giám sát thực tế.

---

## 8. Danh mục kịch bản kiểm thử nghiệm thu RBAC

| # | Tình huống kiểm thử | Kết quả mong đợi |
|---:|---|---|
| 1 | Đăng ký tài khoản hợp lệ | `201 Created`, vai trò luôn là `LEARNER`. |
| 2 | Đăng ký cố tình truyền `role: "INSTRUCTOR"` | `422 Unprocessable Entity`, từ chối tạo tài khoản. |
| 3 | Đăng nhập sai email hoặc mật khẩu | `401 Unauthorized` với thông điệp chung. |
| 4 | Tài khoản có `status: "DISABLED"` đăng nhập | `403 Forbidden`, không cấp token. |
| 5 | Người học A đọc phiên của Người học A | `200 OK`. |
| 6 | Người học A sửa URL để xem phiên của Người học B | `404 Not Found` (không lộ thông tin phiên B). |
| 7 | Người học gọi endpoint `/api/v1/teacher/sessions` | `403 Forbidden`. |
| 8 | Giảng viên đọc phiên chưa được cấp quyền (chưa có grant) | `404 Not Found`. |
| 9 | Giảng viên đọc phiên đã được grant trong `instructor_session_access` | `200 OK`. |
| 10 | Giảng viên gọi `PATCH /sessions/{id}/status` | `403 Forbidden` (chỉ chủ phiên được điều khiển). |
| 11 | Người học tạm dừng phiên thi `EXAM` | `400 Bad Request: EXAM_PAUSE_NOT_ALLOWED`. |
| 12 | AI_LEARNING cố phát sự kiện `MULTIPLE_FACES_DETECTED` (của AI_EXAM) | `403 Forbidden`. |
| 13 | Dùng lại Refresh token đã bị thu hồi hoặc hết hạn | `401 Unauthorized`. |
| 14 | Logout xong dùng lại refresh cookie cũ | `401 Unauthorized`. |
