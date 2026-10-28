# Taxonomy sự kiện — DRAFT (T01/T02/T04)

Quyết, Huy và Phúc cần xác nhận mã, định nghĩa và phép đo; Nam xác nhận câu hiển thị. Các tên sau là đề xuất, chưa phải danh mục chính thức. Không có ngưỡng mặc định.

| Mã đề xuất | Nội dung quan sát | Giới hạn diễn giải |
| --- | --- | --- |
| EYES_CLOSED | Dấu hiệu mắt nhắm trong một khoảng | Không kết luận buồn ngủ/giảm tập trung |
| MOUTH_OPEN | Dấu hiệu miệng mở trong một khoảng | Không tự gọi là ngáp; có thể đang nói |
| HEAD_TURNED | Hướng đầu thay đổi theo tiêu chí đã hiệu chỉnh | Không đo trực tiếp hướng nhìn hoặc ý định |
| FACE_NOT_DETECTED | Không phát hiện khuôn mặt trong khung hình hợp lệ | Không khẳng định đã rời chỗ; xem ánh sáng/góc camera |
| MULTIPLE_FACES | Phát hiện nhiều khuôn mặt | Không xác định danh tính hay kết luận hỗ trợ gian lận |
| TAB_HIDDEN | Trang chuyển sang trạng thái không hiển thị | Nguồn browser; không khẳng định nội dung tab khác |

WBS T09 ghi “yawning” và “face missing”; bản nháp dùng MOUTH_OPEN và FACE_NOT_DETECTED để tránh suy diễn vượt tín hiệu. Đây là đề xuất thuật ngữ cần nhóm chốt, không sửa WBS. Nếu định nghĩa yawning được xác lập và đánh giá sau này, cần cập nhật taxonomy/schema qua PR.

Chỉ dùng “kéo dài” khi rule thời gian đã được chốt và sự kiện đáp ứng rule đó. Severity là mức ưu tiên hiển thị, không phải xác suất gian lận; hiện để null vì chính sách chưa xác định. Sự cố camera và dữ liệu thiếu là trạng thái kỹ thuật riêng, không gộp vào số hành vi.
