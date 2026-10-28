# Kiến trúc tích hợp — DRAFT

## Luồng và ranh giới

Webcam/Video → AI Core → Raw Signals → Event Engine → Event API/WebSocket → Frontend.
AI Core trả phép đo và trạng thái chất lượng. Event Engine xác định khoảng sự kiện theo rules được hiệu chỉnh. Backend kiểm tra contract/quyền, lưu và phân phối. Frontend diễn giải trung tính và cho người dùng biết giới hạn.

Browser visibility là nhánh tín hiệu riêng từ frontend; không giả dạng raw webcam. `TAB_HIDDEN` chỉ có nghĩa trang không hiển thị, không khẳng định chuyển sang tab cụ thể hoặc gian lận. Camera giám sát, phone detection và nhận diện danh tính chưa thuộc contract này.

## Phát triển độc lập

| Module | Fixture | Điều có thể làm ngay |
| --- | --- | --- |
| AI Core | raw-signals.sample.json | Đối chiếu hình dạng đầu ra dự kiến |
| Event Engine | raw-signals.sample.json, raw-signals.unavailable.json | Thiết kế xử lý phép đo/thiếu dữ liệu |
| Backend | event.sample.json, event.browser.json | Thảo luận validation, quyền và mapping |
| Frontend | event.sample.json, event.browser.json | Prototype hiển thị, giải thích, trạng thái |

Các file tại `shared/examples/` chỉ là mẫu contract, không phải chuỗi đủ để chứng minh rule kích hoạt. Timeline thử rule cần được Huy xây trong T04/T09 theo ngưỡng đã thống nhất. UI phải hiện rõ DEMO khi dùng fixture.

## Thời gian và lỗi — đề xuất cần duyệt

- `timestamp`: UTC RFC 3339 kết thúc bằng Z; thời điểm ghi nhận tại nguồn, không phải lúc server nhận.
- `offset_ms`: thời gian tương đối từ đầu phiên/nguồn, dùng để tính khoảng thời gian; `sequence`: số thứ tự frame, tăng trong một session/source.
- Chốt cách đồng bộ clock/session cho video offline và webcam ở T02/T15. Consumer không dùng thời gian mạng đến để suy ra thời lượng mắt nhắm.
- Đề xuất phân biệt `ok`, `degraded`, `unavailable`. `null` là không đo được; 0 là đo được giá trị 0. Không biến mất tín hiệu thành FACE_NOT_DETECTED.
- Mất frame, mất kết nối, đảo thứ tự, trùng message và thay nguồn phải có chính sách trước tích hợp T19. Không tuyên bố exactly-once hay replay nếu chưa triển khai.
- Event mock đang biểu diễn khoảng đã kết thúc; cơ chế start/update/end realtime vẫn cần chốt, chưa được schema này bảo đảm.
- Huy xử lý debounce/nhiễu và vòng đời rule; Phúc giới hạn tần suất thông báo hiển thị. Lưu event và hiển thị cảnh báo là hai việc khác nhau, không được vô tình xóa bằng chứng chỉ vì cooldown UI.

## Cần thống nhất

Vị trí chạy AI, cách truyền hình ảnh, nguồn clock, cấu hình extraction, hệ trục, retention và transport đều chưa chốt. Mặc định thiết kế hướng tối thiểu hóa dữ liệu; không đưa ảnh/video/landmarks nhận diện vào event payload. Xem [các quyết định mở](../decisions-pending.md).
