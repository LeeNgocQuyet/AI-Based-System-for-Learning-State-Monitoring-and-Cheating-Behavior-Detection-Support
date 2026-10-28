# Evaluation — kế hoạch DRAFT

Huy chủ trì; Quyết phối hợp đo AI, Phúc đo truyền/lưu và phân quyền, Nam phối hợp HCI. Liên quan T04/T10/T20/T22/T24/T28. Chưa có dữ liệu đo hoặc kết quả.

## Đơn vị và quy trình

Tách độ ổn định/phép đo ở mức frame khỏi Precision/Recall/F1 ở mức event. Định nghĩa nhãn theo hành vi quan sát được; ghi onset/offset, khoảng không xác định và chất lượng hình ảnh. Không gán nhãn gian lận/giảm tập trung từ video.

Trước T22 cần chốt quy tắc ghép event dự đoán với nhãn: cùng loại, tiêu chí overlap hoặc sai số thời gian, ghép một-một, xử lý duplicate và khoảng thiếu dữ liệu. Chưa đặt con số tolerance/threshold. Tách dữ liệu hiệu chỉnh và test theo người/phiên để tránh rò rỉ; không tune trên test cuối. Ghi số người, số video, thời lượng, số event từng loại và giới hạn mẫu.

Precision = TP/(TP+FP), Recall = TP/(TP+FN); F1 tính khi có mẫu đủ nghĩa. Nếu mẫu số bằng 0 báo N/A kèm lý do. Báo false positives theo loại và theo đơn vị thời gian quan sát hợp lệ; không lấy mock làm kết quả. Thống nhất cách thể hiện confusion matrix cho event và mẫu nền trước khi báo cáo.

Đề xuất hai người gán nhãn độc lập một phần dữ liệu, lưu bất đồng và cách phân xử; tỷ lệ phần gán nhãn đôi và người thực hiện cần nhóm chốt. Chỉ dùng video có quyền sử dụng/đồng thuận.

## Ma trận tình huống cần thiết kế

| Tình huống | Điều cần kiểm tra |
| --- | --- |
| Nhắm mắt/chớp mắt | Tách dấu hiệu ngắn và khoảng theo rule đã chốt |
| Nói chuyện/miệng mở | Không tự suy ra ngáp |
| Quay/cúi đầu | Nhiễu pose và giới hạn diễn giải |
| Không có mặt/che khuất/ánh sáng yếu | Phân biệt phép đo face_count=0 và không đo được |
| Nhiều mặt/kính/góc webcam | Độ ổn định và failure cases |
| FPS biến động/mất frame | Tính theo thời gian; không suy diễn frame thiếu |
| Mất mạng/trùng event/đảo thứ tự | Hành vi transport được định nghĩa, không mất dấu âm thầm |
| Sửa session_id/role | Không xem chéo dữ liệu ở API và WebSocket khi được hiện thực |

Hiệu năng: ghi cấu hình máy, phiên bản model/dependencies, resolution, điều kiện ánh sáng, FPS, latency từng đoạn/end-to-end và tài nguyên; phân biệt mục tiêu với số đo. Chưa có mức FPS/latency nghiệm thu mặc định.

HCI dùng [protocol DRAFT](hci-protocol.md). Metrics kỹ thuật không thay thế công bằng cảm nhận, khả năng kiểm soát, mức gây phiền và hiểu đúng cảnh báo.
