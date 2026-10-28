# Quản lý dữ liệu và bảo mật

## Nguyên tắc phối hợp

Chỉ thu dữ liệu cần cho mục tiêu đã công bố. Quyền camera trên trình duyệt không thay thế đồng thuận tham gia nghiên cứu hoặc đồng thuận ghi/lưu video. Trước thu thập, thông báo mục đích, trường dữ liệu, ai được xem, nơi lưu, thời hạn xóa và cách yêu cầu rút lui. Cần thống nhất với giảng viên/quy trình của trường trước khi tuyển người tham gia; đây là hướng dẫn dự án, không phải tư vấn pháp lý.

Không mặc định ghi video. Nếu cần video để gán nhãn/evaluation, xin đồng thuận riêng, nêu rõ phạm vi sử dụng, không dùng cho chấm điểm hoặc kỷ luật. Từ chối hoặc dừng tham gia không ảnh hưởng điểm học tập. Không công khai video hoặc dữ liệu thô cùng repository public.

## Quyền truy cập dự kiến

| Dữ liệu | Quyền tối thiểu |
| --- | --- |
| Lịch sử phiên người học | Chính người học và giảng viên được giao phiên |
| Video thu cho evaluation | Thành viên được phân công xử lý/gán nhãn, theo đồng thuận |
| Bảng nối mã nghiên cứu với danh tính | Người quản lý dữ liệu được nhóm chỉ định; lưu riêng |
| Kết quả tổng hợp | Chỉ công bố sau kiểm tra khả năng nhận diện lại |

Mã session hoặc mã nghiên cứu là giả danh, không tự động có nghĩa đã ẩn danh. Dữ liệu thật đặt ngoài Git, trong kho giới hạn quyền; quyết định người quản lý, lưu trữ, mã hóa, retention và lịch xóa trước khi thu. Xóa cả bản sao/backup theo chính sách đã thông báo, ghi nhận việc xóa. Nếu đã tổng hợp/ẩn danh không thể nối ngược, giới hạn rút dữ liệu phải giải thích trước.

## Repository và vận hành

- Không commit `.env`, credentials, tokens, private keys, webcam recordings, ảnh người thật, dataset nhạy cảm, DB dumps hoặc dữ liệu bảng hỏi cá nhân.
- `.env.example` chỉ chứa tên cấu hình và placeholder an toàn khi thực sự cần; không sao chép secret đang dùng.
- `.gitignore` giảm sai sót, không phát hiện hết dữ liệu cá nhân; review cả diff, notebook output, screenshots và logs.
- Không đưa dữ liệu thật lên issue/PR hoặc CI artifacts. CI hiện chỉ dùng dữ liệu tổng hợp, không truy cập webcam và không dùng secrets.
- Dataset công khai vẫn cần kiểm tra giấy phép/quyền sử dụng và điều kiện thu thập; ghi nguồn, không mặc định được phép tái phát hành.
- Khi có backend: kiểm tra ownership/role ở API và WS, giới hạn dữ liệu trả về, không dựa vào ẩn nút frontend.

Các quyết định này phải cụ thể hóa ở T10/T11/T20/T23/T27 trước thu dữ liệu và user study.
