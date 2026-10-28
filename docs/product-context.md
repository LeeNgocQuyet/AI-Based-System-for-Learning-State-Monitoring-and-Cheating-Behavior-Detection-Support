# Căn cứ sản phẩm và đối chiếu WBS

Nguồn: ba tài liệu người dùng cung cấp ngày 28/10/2026 (báo cáo tiến độ nhóm 3, WBS T01–T32, đặc tả UI/UX S01–S12) và nhận xét giảng viên. Tài liệu này tóm tắt để phối hợp; không thay thế hay tự sửa WBS gốc.

## Điều chỉnh theo nhận xét giảng viên

Giữ bối cảnh học tập/thi nhưng không coi tín hiệu webcam là phép đo giảm tập trung, buồn ngủ hay gian lận. Taxonomy và nội dung cảnh báo dùng hành vi quan sát được, giải thích nhiễu và tình trạng không đo được. HCI phải đo perceived fairness, control, annoyance và comprehension thay vì chỉ hỏi mức hài lòng.

## Phạm vi và màn hình

Hai vai trò người học/giảng viên; hai chế độ học/thi. Luồng UI gốc: S01 đăng nhập; S02 đăng ký người học; S03 quên mật khẩu; S04 trang chủ; S05/S07 chuẩn bị camera; S06/S08 phiên học/thi; S09 tóm tắt/lịch sử; S10 dashboard; S11 chi tiết; S12 báo cáo.

Không bật camera lúc login; giải thích mục đích trước cấp quyền. Người học không tự cấp vai trò giảng viên. Hiển thị rõ loading/empty/error/disconnected và không đủ quyền. Nút pause, đánh dấu đã xem, xuất báo cáo và cách cấp tài khoản giảng viên còn cần chốt theo đặc tả. Camera góc rộng là hướng mở rộng; nhận diện điện thoại là tùy chọn, chưa đưa vào schema.

## Liên hệ nền tảng với WBS

| WBS hiện có | Nền tảng được chuẩn bị | Chưa được coi là hoàn thành |
| --- | --- | --- |
| T01 | Phạm vi, nguyên tắc diễn giải, taxonomy DRAFT | Đồng thuận MVP/taxonomy |
| T02 | Raw/event schema DRAFT, mock và ghi chú API | Schema v1 chính thức, OpenAPI và contract đã duyệt |
| T04 | Ranh giới rules, nhãn và ma trận đánh giá | Onset/offset, thresholds, tiêu chí matching đã chốt |
| T05/T06 | Mô tả UI liên quan và protocol HCI DRAFT | Figma/prototype, bảng hỏi/protocol đã duyệt |
| T20/T22 | Kế hoạch split/metrics | Dữ liệu gán nhãn và kết quả đo |
| T23/T27/T28 | Pilot 3–5, mục tiêu study 20–24, AB/BA từ WBS | Tuyển người, chạy nghiên cứu và phân tích |

Các task hiện thực T03, T07–T19 và đóng gói/bàn giao tiếp theo vẫn thuộc kế hoạch gốc; scaffold không tạo task mới và không tự cập nhật trạng thái.

WBS có dòng lịch “tuần thứ 8 ... (25/10 - 1/10)” không nhất quán; cần nhóm xác nhận mốc lịch. Không tự suy đoán ngày kết thúc. Tên đầy đủ/MSSV thành viên chưa cung cấp, không tự điền.
