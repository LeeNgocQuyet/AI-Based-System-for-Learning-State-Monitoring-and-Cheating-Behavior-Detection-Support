# EduFocus Frontend

Giao diện web SPA (Single Page Application) cho hệ thống **EduFocus** — hỗ trợ theo dõi trạng thái học tập và phát hiện hành vi gian lận trong phòng thi trực tuyến.

> **Phạm vi:** Toàn bộ code frontend nằm trong thư mục `frontend/app/`. Không có phụ thuộc backend trong bản này — hoạt động hoàn toàn với mock data.

---

## Khởi chạy

```bash
# Dùng npx serve (khuyến nghị, không cần cài thêm)
npx serve frontend/app

# Hoặc dùng Python 3
cd frontend/app
python -m http.server 8080

# Hoặc dùng Node.js http-server
npx http-server frontend/app -p 8080
```

Sau đó mở trình duyệt tại: **http://localhost:3000** (hoặc port tương ứng)

> ⚠️ **Lưu ý:** WebRTC (`getUserMedia`) chỉ hoạt động trên `localhost` hoặc HTTPS. Nếu mở bằng `file://` thì camera sẽ không hoạt động (nhưng các chức năng khác vẫn chạy).

---

## Tài khoản demo

| Vai trò     | Email                 | Mật khẩu  |
|-------------|----------------------|-----------|
| Giảng viên  | `teacher@demo.test`   | `12345678` |
| Sinh viên   | `student@demo.test`   | `12345678` |

> Nhấn **"Đặt lại dữ liệu demo"** trên màn hình đăng nhập để xóa localStorage và khôi phục trạng thái ban đầu.

---

## Luồng sử dụng

### Luồng giảng viên
1. Đăng nhập → Trang chủ giảng viên
2. Chọn lớp học phần → Nhấn **"Mở phiên mới"**
3. Chọn loại phiên (học / thi), nhập tên → Xác nhận
4. Vào **Dashboard phiên** → Nhấn **"Mô phỏng điểm danh"**
5. Xem camera wall, danh sách sinh viên, ảnh minh chứng
6. Nhấn tên sinh viên để xem chi tiết
7. Nhấn **"Kết thúc phiên"** khi xong

### Luồng sinh viên
1. Đăng nhập → Trang chủ sinh viên
2. Chọn lớp đang có phiên → Nhấn **"Tham gia"**
3. Trang chuẩn bị: Nhấn **"Bật camera"** (thực) → Kiểm tra → Nhấn **"Tham gia phiên"**
4. Màn hình phiên: Đồng hồ đếm giờ thực, xem sự kiện đã ghi nhận
5. Nhấn **"Rời phiên"** để kết thúc

---

## Tính năng

### Thực (browser APIs)
| Tính năng | API sử dụng |
|-----------|------------|
| Webcam thật | `navigator.mediaDevices.getUserMedia()` |
| Đồng hồ phiên | `setInterval` + `sessionStorage` |
| Ghi nhận chuyển tab | `document.visibilitychange` (Page Visibility API) |
| Lưu trạng thái đăng nhập | `sessionStorage` |
| Lưu dữ liệu phiên & sự kiện | `localStorage` |

### Mock (dữ liệu mô phỏng)
| Tính năng | Ghi chú |
|-----------|---------|
| Camera giảng viên xem sinh viên | Mock SVG frames (giao diện minh họa) |
| Trạng thái ổn định / cần xem xét / lỗi | Sinh ngẫu nhiên khi seed attendance |
| Phân tích AI | Chưa tích hợp — slot để gọi API sau |
| Truyền video peer-to-peer | Chưa có WebRTC P2P |

---

## Cấu trúc thư mục

```
frontend/app/
├── index.html              # Entry point SPA
├── css/
│   ├── variables.css       # CSS custom properties
│   ├── layout.css          # Topbar, sidebar, shell, grid
│   ├── components.css      # Button, card, badge, modal, toast…
│   ├── pages.css           # Màn hình cụ thể (auth, live, prepare…)
│   ├── camera.css          # Camera wall, mock frames, evidence
│   └── responsive.css      # Media queries
└── js/
    ├── main.js             # Entry point: router + event delegation
    ├── router.js           # SPA router với role guards
    ├── auth.js             # Đăng nhập / đăng ký / logout
    ├── data.js             # Mock DB + localStorage CRUD
    ├── camera.js           # WebRTC getUserMedia wrapper
    ├── events.js           # Page Visibility tracking
    ├── session.js          # Timer (setInterval) + pause/resume
    ├── ui.js               # Toast, modal, badge, helpers
    └── pages/
        ├── shell.js            # Header + sidebar (authenticated)
        ├── mock-camera.js      # Mock SVG camera frames
        ├── login.js
        ├── register.js
        ├── forgot.js
        ├── teacher-home.js
        ├── teacher-course.js
        ├── teacher-session.js  # Dashboard phiên
        ├── teacher-student.js  # Chi tiết sinh viên
        ├── teacher-reports.js
        ├── student-home.js
        ├── student-course.js
        ├── student-prepare.js  # Kiểm tra webcam
        ├── student-live.js     # Phiên đang diễn ra
        └── student-history.js
```

---

## Kiến trúc

- **Vanilla JS ES Modules** — không cần build step, không framework
- **SPA Router** — điều hướng bằng `navigate(route, params)`, lưu route vào `sessionStorage`
- **Event delegation** — một listener duy nhất tại `document` xử lý tất cả click
- **Page lifecycle** — mỗi route có `renderXxx()` → HTML string và `initXxx()` → DOM setup
- **Data layer** — `data.js` cung cấp tất cả CRUD functions; thay `localStorage` bằng `fetch()` để kết nối backend

---

## Giới hạn đã biết

| Giới hạn | Giải thích |
|---------|------------|
| Camera sinh viên trên dashboard giảng viên là giả | Cần WebRTC P2P / media server cho tính năng thật |
| Phân tích AI là mock | Cần tích hợp AI API và thay thế `seedAttendance()` |
| Không có real-time sync | Cần WebSocket để đồng bộ trạng thái thật giữa các tab/thiết bị |
| Dữ liệu mất khi reset localStorage | Dùng backend DB để persistent data thật |
| Không có HTTPS tự ký | Camera chỉ hoạt động trên localhost hoặc HTTPS server |

---

## Phát triển thêm

Để tích hợp backend:
1. Mở `js/data.js` → thay các hàm `getData/saveData` bằng `fetch()` calls
2. Mở `js/auth.js` → thay `sessionStorage` bằng JWT / cookie từ API
3. Mở `js/camera.js` → thêm WebRTC signaling để stream camera thật
4. Mở `js/events.js` → gửi events lên server qua WebSocket thay vì chỉ lưu local

---

*EduFocus Frontend — Phiên bản demo (Vanilla JS ES Modules, không cần build)*
