# Contract API/WebSocket — DRAFT (T02)

Phúc chủ trì, Quyết và Huy đồng thuận ngữ nghĩa dữ liệu, Nam phản hồi nhu cầu màn hình. Đây là tài liệu ranh giới, chưa phải REST API, OpenAPI hoàn chỉnh hoặc lựa chọn framework.

## Producer / consumer

| Trao đổi | Đầu vào | Đầu ra dự kiến |
| --- | --- | --- |
| AI Core → Event Engine | Frame/video được phép | Raw signals schema |
| Event Engine → Backend | Event schema | Kết quả tiếp nhận cần chốt |
| Browser → Backend | TAB_HIDDEN qua contract nguồn browser | Event đã kiểm tra phiên/quyền |
| Backend → Frontend | Event đã phân quyền | Cùng ngữ nghĩa event qua API/WS |

Đọc schema và examples từ `shared/`; hiện có thể dùng trực tiếp file JSON để prototype, không cần server mock.

## T02 còn phải chốt

- Endpoints/methods, OpenAPI draft, envelope WebSocket, lỗi và versioning transport.
- Tạo/bắt đầu/kết thúc phiên và sự khác nhau giữa session, người học và nguồn camera.
- Auth/RBAC: người học chỉ xem phiên của mình; giảng viên chỉ xem phiên được cấp quyền. Backend kiểm tra mọi yêu cầu/đăng ký WebSocket; không tin role hoặc session_id do client tự khai.
- Idempotency theo event_id; retry, mất mạng, thứ tự và reconnect/replay; không có bảo đảm lưu khi offline trong nền tảng hiện tại.
- Pagination/filter, timestamp nhận ở server, retention, xử lý phiên đóng và event đến muộn.
- Vòng đời event realtime start/update/end so với interval đã kết thúc trong mẫu hiện tại.
- Severity, nơi sinh thông điệp UI, chính sách hiển thị học/thi và giới hạn tần suất.

Schema DRAFT không phải API public ổn định; chưa đánh dấu T02 hoàn thành. Không nhúng secret hoặc ảnh/video vào payload; không log đầy đủ thông tin cá nhân khi validation lỗi.
