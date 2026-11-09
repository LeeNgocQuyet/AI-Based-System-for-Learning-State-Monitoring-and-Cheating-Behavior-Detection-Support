# Backend Architecture, Session/Event API & Seed Data v1.2 — Nhóm 3

**Đề tài:** Thiết kế và phát triển hệ thống giám sát trạng thái học tập và hỗ trợ phát hiện hành vi gian lận dựa trên trí tuệ nhân tạo.

**Phiên bản:** Release v1.2.0 — Triển khai hoàn chỉnh FastAPI Service, Session Lifecycle API, Event Ingestion/Query API, Postman Test Suite, và Dữ liệu Mock Seeding phục vụ Frontend phát triển độc lập.

---

## 1. Cấu trúc thư mục Backend v1.2

Thư mục `backend/` được tổ chức theo chuẩn kiến trúc phân tầng (Clean Architecture / Layered Pattern):

```
backend/
├── app/                           # Mã nguồn chính ứng dụng FastAPI
│   ├── main.py                    # Entry point khởi tạo FastAPI app, middleware CORS, định tuyến
│   ├── api/v1/                    # Tầng Controller / Endpoints (Sessions, Events, Teacher)
│   │   ├── sessions.py            # API tạo phiên, pause, resume, end, xem chi tiết và báo cáo
│   │   ├── events.py              # API ingest sự kiện (idempotent) và query sự kiện
│   │   ├── teacher.py             # API danh sách phiên dành cho Giảng viên (grant scope)
│   │   └── router.py              # Gom các router API v1
│   ├── core/                      # Cấu hình bảo mật, JWT dependencies, Settings
│   │   ├── config.py              # Pydantic Settings đọc biến môi trường
│   │   ├── dependencies.py        # Dependency injection xác thực Token (Learner/Instructor/Service)
│   │   └── security.py            # Logic mã hóa mật khẩu và decode/encode JWT token
│   ├── db/                        # Kết nối cơ sở dữ liệu SQLAlchemy 2.0
│   │   ├── base.py                # DeclarativeBase chung cho models
│   │   └── session.py             # SessionLocal và dependency get_db
│   ├── models/                    # ORM Models ánh xạ bảng CSDL PostgreSQL
│   │   ├── enums.py               # Enums chuẩn (UserRole, SessionType, SessionStatus, EventType, Severity, Source)
│   │   ├── user.py                # Model User
│   │   ├── session.py             # Model LearningSession (tính duration, ràng buộc state)
│   │   ├── event.py               # Model Event (idempotency, severity, message, is_reviewed)
│   │   └── instructor_access.py   # Model InstructorSessionAccess (allow-list grants)
│   ├── schemas/                   # Pydantic Schemas xác thực DTO Request/Response
│   │   ├── session.py             # Schema SessionCreate, SessionOut, SessionReport
│   │   └── event.py               # Schema EventIngest (validate UTC, source mapping), EventOut
│   └── services/                  # Business Logic Layer
│       ├── session_service.py     # Quản lý vòng đời phiên, tính thời lượng active, RBAC scope
│       └── event_service.py       # Ingest sự kiện, chuẩn hóa severity demo, deduplication
├── database/                      # DDL khởi tạo cơ sở dữ liệu PostgreSQL
│   ├── schema-v1.sql              # Schema DDL chuẩn: users, sessions, events, grants, refresh_tokens
│   ├── seed_instructor.py         # Script khởi tạo tài khoản Giảng viên với Argon2id
│   └── grant-instructor-session.sql # Script phân quyền phiên mẫu cho Giảng viên
├── scripts/                       # Các script công cụ vận hành và kiểm thử
│   ├── seed_demo.py               # Seed CSDL: 2 learner, 1 instructor, 2 sessions và mock events
│   ├── issue_user_token.py        # Sinh Access JWT cho Learner/Instructor phục vụ Swagger/Postman
│   ├── issue_service_token.py     # Sinh Service Token cho AI_LEARNING / AI_EXAM / SYSTEM
│   └── grant_instructor_session.py # Cấp quyền đọc phiên cho Giảng viên
├── postman/                       # Bộ kiểm thử Postman hoàn chỉnh
│   ├── collection-session-event-v1.2.json # Postman Collection kiểm thử trọn vẹn Session & Event
│   └── environment.template.json  # Postman Environment Template mẫu
├── seed/                          # Dữ liệu Mock tĩnh cho Frontend
│   └── frontend-mock-sessions.json # Response fixtures tĩnh giúp Frontend phát triển độc lập
├── tests/                         # Bộ kiểm thử tự động pytest (19/19 test cases)
│   ├── conftest.py                # Fixtures SQLite in-memory, mock JWT credentials
│   ├── test_sessions.py           # Unit tests kiểm thử vòng đời phiên và RBAC
│   └── test_events.py             # Unit tests kiểm thử event ingest, idempotency, source spoofing
├── docs/                          # Tài liệu kỹ thuật tham chiếu
│   ├── openapi-session-event-v1.2.json # OpenAPI 3.1 JSON sinh trực tiếp từ FastAPI
│   └── api-contract-delta-v1.2.md      # Chi tiết các delta cải tiến v1.2
├── Dockerfile                     # Đóng gói container ứng dụng Backend
├── docker-compose.yml             # Khởi chạy trọn gói PostgreSQL 15 + API + Auto Seed
├── requirements.txt               # Thư viện runtime (FastAPI, SQLAlchemy, psycopg, PyJWT, pydantic)
├── requirements-dev.txt           # Thư viện development & testing (pytest, httpx)
├── pytest.ini                     # Cấu hình test runner
└── .env.example                   # Mẫu cấu hình môi trường
```

---

## 2. Các chức năng Session/Event API cốt lõi (v1.2)

### 2.1. Quản lý Vòng đời Phiên (Session Lifecycle)
- **Tạo và bắt đầu phiên (`POST /api/v1/sessions`):**
  - Người học tạo phiên `LEARNING` hoặc `EXAM`. Hệ thống khởi tạo trạng thái `ACTIVE` ngay lập tức.
  - Tự động gán `started_at` và `active_started_at = NOW()`.
- **Xem phiên cá nhân (`GET /api/v1/sessions/mine`):**
  - Trả về danh sách phiên của chính sinh viên đang đăng nhập, hỗ trợ phân trang và lọc theo trạng thái/thời gian.
- **Tạm dừng, Tiếp tục, Kết thúc:**
  - `PATCH /api/v1/sessions/{session_id}/status` với body `{"status": "PAUSED" | "ACTIVE" | "ENDED"}`.
  - `POST /api/v1/sessions/{session_id}/start`: Tiện ích resume phiên đang tạm dừng (`PAUSED -> ACTIVE`).
  - `POST /api/v1/sessions/{session_id}/end`: Tiện ích kết thúc phiên (`ENDED`).
  - **Quy tắc an toàn thi cử:** Chế độ `EXAM` tuyệt đối cấm chuyển sang trạng thái `PAUSED` (trả về lỗi `400 EXAM_PAUSE_NOT_ALLOWED`).
- **Thời lượng giám sát thực tế (`duration_ms`):**
  - Chỉ tính tổng thời gian ở trạng thái `ACTIVE`. Toàn bộ khoảng thời gian `PAUSED` bị loại trừ hoàn toàn.

### 2.2. Ingest và Truy vấn Sự kiện (Event Ingestion & Query)
- **Tiếp nhận sự kiện (`POST /api/v1/sessions/{session_id}/events`):**
  - Hỗ trợ đúng 1 event/request theo chuẩn `EventIngest`.
  - **Idempotency (Chống trùng lặp):** Gửi lại cùng `event_id` với payload giống hệt sẽ trả về `200 OK` kèm bản ghi cũ. Nếu cùng ID nhưng payload bị sửa đổi sẽ trả về `409 Conflict`.
  - **Phân quyền nguồn phát (Source Integrity):**
    - Token người học chỉ được gửi sự kiện `source: BROWSER` (`TAB_HIDDEN`, `CAMERA_LOST`) cho chính phiên của mình.
    - Token AI Service chỉ được phát sự kiện khớp với quyền được cấp (`AI_LEARNING` vào phiên `LEARNING`, `AI_EXAM` vào phiên `EXAM`).
  - **Chuẩn hóa tự động:** Backend tự động gán `received_at`, thông điệp trung tính và mức độ `severity` (`INFO`, `LOW`, `MEDIUM`, `HIGH`).
- **Truy vấn sự kiện (`GET /api/v1/sessions/{session_id}/events`):**
  - Cho phép người học (xem phiên của mình) và giảng viên (xem phiên có grant) tra cứu danh sách sự kiện kèm bộ lọc theo loại, mức độ, nguồn, thời gian.
- **Báo cáo thống kê phiên (`GET /api/v1/sessions/{session_id}/report`):**
  - Tổng hợp số lượng sự kiện theo từng loại (`counts_by_type`) và theo mức độ nghiêm trọng (`counts_by_severity`).

---

## 3. Dữ liệu Mock phục vụ Frontend phát triển độc lập

Frontend có thể phát triển hoàn toàn độc lập thông qua 2 phương án:

1. **Phương án Mock Tĩnh (Offline Fixtures):**
   - Sử dụng tệp [`backend/seed/frontend-mock-sessions.json`](file:///E:/Project_CV/BTL_TuongTacNguoiMay/AI-Based-System-for-Learning-State-Monitoring-and-Cheating-Behavior-Detection-Support/backend/seed/frontend-mock-sessions.json).
   - Chứa sẵn cấu trúc JSON Response hoàn chỉnh của các API: tạo phiên (`session_create_response`), tạm dừng (`session_pause_response`), kết thúc (`session_end_response`), danh sách sự kiện (`event_list_response`) với đầy đủ 3 loại sự kiện mẫu (`EYES_CLOSED_LONG`, `YAWN_DETECTED`, `TAB_HIDDEN`).
2. **Phương án Chạy Backend Mock Seeding (Live Demo API):**
   - Chạy script `python scripts/seed_demo.py` để nạp sẵn:
     - 2 tài khoản sinh viên: `learner.one@example.edu` và `learner.two@example.edu`.
     - 1 tài khoản giảng viên: `instructor.demo@example.edu`.
     - 2 phiên làm việc mẫu (1 phiên `LEARNING` đã kết thúc kèm 5 sự kiện; 1 phiên `EXAM` kèm 3 sự kiện và grant sẵn cho giảng viên).

---

## 4. Hướng dẫn Khởi chạy & Kiểm thử

### Cách 1: Khởi chạy nhanh bằng Docker Compose (Khuyên dùng)
```bash
cd backend
cp .env.example .env
docker compose up --build
```
Hệ thống tự động:
1. Tạo container PostgreSQL 15 và thực thi `database/schema-v1.sql`.
2. Chạy `scripts/seed_demo.py` nạp sẵn dữ liệu demo.
3. Khởi động FastAPI server tại `http://localhost:8000`.

* **Swagger UI:** `http://localhost:8000/api/v1/docs`
* **OpenAPI JSON:** `http://localhost:8000/api/v1/openapi.json`
* **Health Check:** `http://localhost:8000/health`

### Cách 2: Khởi chạy Local bằng Python Virtualenv
```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Cài đặt thư viện:
pip install -r requirements-dev.txt

# Tạo file .env và cấu hình DATABASE_URL
cp .env.example .env

# Chạy seed dữ liệu demo:
python scripts/seed_demo.py

# Khởi chạy API server:
uvicorn app.main:app --reload --port 8000
```

---

## 5. Kiểm thử qua Postman & Swagger

### Bước 1: Phát Token kiểm thử
Khi chưa kết nối module Auth tập trung, sử dụng script phát Token nội bộ:
```bash
# Token sinh viên:
python scripts/issue_user_token.py --email learner.one@example.edu
# Token giảng viên:
python scripts/issue_user_token.py --email instructor.demo@example.edu
# Token AI Service:
python scripts/issue_service_token.py --service ai-learning
python scripts/issue_service_token.py --service ai-exam
```

### Bước 2: Chạy Postman Collection
1. Mở Postman $\rightarrow$ Import tệp [`backend/postman/collection-session-event-v1.2.json`](file:///E:/Project_CV/BTL_TuongTacNguoiMay/AI-Based-System-for-Learning-State-Monitoring-and-Cheating-Behavior-Detection-Support/backend/postman/collection-session-event-v1.2.json).
2. Import Environment template [`backend/postman/environment.template.json`](file:///E:/Project_CV/BTL_TuongTacNguoiMay/AI-Based-System-for-Learning-State-Monitoring-and-Cheating-Behavior-Detection-Support/backend/postman/environment.template.json).
3. Dán các token vừa sinh vào biến `learnerToken`, `instructorToken`, `aiLearningToken`, `aiExamToken`.
4. Thực thi tuần tự các request:
   - `Create Learning Session` (Tạo phiên học tập $\rightarrow$ lưu `sessionId`)
   - `Ingest Browser Event` (Bắn sự kiện `TAB_HIDDEN`)
   - `Ingest AI Learning Event` (Bắn sự kiện `EYES_CLOSED_LONG`)
   - `Idempotent Retry` (Gửi lại cùng `event_id` $\rightarrow$ kiểm tra phản hồi `200 OK`)
   - `Get Session Events` & `Get Session Report`
   - `Pause Session` $\rightarrow$ `Resume Session (Start)` $\rightarrow$ `End Session`
   - `Teacher List Sessions` (Giảng viên kiểm tra phiên có grant)

### Bước 3: Chạy Unit Tests tự động
```bash
pytest
```
Bộ kiểm thử gồm 19 test cases tự động chạy trên SQLite in-memory, kiểm chứng đầy đủ tính đúng đắn của logic vòng đời phiên, chống gian lận nguồn phát, cơ chế retry idempotent và ma trận phân quyền RBAC.
