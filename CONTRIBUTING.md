# Quy trình đóng góp

## Nhánh và Pull Request

`main` là nhánh ổn định. Mọi thay đổi nội dung vào `main` phải qua Pull Request; không push trực tiếp, không force-push main.
Sau khi repository có commit gốc và main:

```bash
git switch main
git pull --ff-only origin main
git switch -c feature/T02-draft-contracts
```

Tên nhánh dùng `feature/Txx-description`, với Task ID thật từ WBS T01–T32. Ví dụ trên là T02 đã có, không tạo một task mới. Một PR có thể liên quan nhiều task, nhưng chọn một Task ID chính cho tên nhánh và liệt kê các task liên quan trong mô tả.

Commit ngắn, rõ, ví dụ `docs(T02): add draft event contract`. Không tự đánh dấu toàn bộ task hoàn thành chỉ vì đã tạo khung tài liệu.

PR phải ghi Task ID, thay đổi, cách kiểm thử và kết quả thực tế, ảnh hưởng module khác, quyết định còn mở. Dùng template có sẵn. Tối thiểu một thành viên khác review trước khi merge. Thay đổi contract cần Quyết, Huy và Phúc cùng xác nhận; đây là quy trình nhóm, không giả định một approval GitHub thay thế đủ ba xác nhận. Nam review phần hiển thị và nội dung cảnh báo.

Tạo Draft PR sớm để thảo luận. Sau review, CI đạt và các trao đổi được xử lý, người có quyền merge mới đưa vào main. Đề xuất squash merge, xóa nhánh đã merge. Không tự thay quyền truy cập hay mời thành viên.

## Làm việc độc lập

- Quyết tạo đầu ra theo raw-signals schema; chưa áp ngưỡng cảnh báo trong AI Core.
- Huy dùng raw-signals mock để thiết kế rules, không cần webcam của Quyết.
- Phúc dùng event mock để thiết kế contract và quyền truy cập.
- Nam dùng event mock để thiết kế màn hình, không chờ API/AI.

Thay đổi schema phải cập nhật version DRAFT, ví dụ, tài liệu đơn vị/null/nguồn và ghi ảnh hưởng consumer. Không âm thầm sửa ý nghĩa một trường đã thống nhất. Dữ liệu thiếu không được đổi thành 0 hoặc suy diễn thành hành vi.

## Kiểm tra trước PR

Chạy lệnh kiểm tra ở README. CI chỉ kiểm tra cấu trúc, JSON Schema, YAML và payload tổng hợp; không chứng nhận chất lượng AI, API, UI hay độ chính xác hành vi. Khi có source thật, bổ sung kiểm thử thích hợp trong task WBS tương ứng, không thêm test luôn-pass hoặc job giả cho module rỗng.

Review diff trước khi commit. Không dùng `git add -f` để đưa dữ liệu bị ignore vào repo. `.gitignore` không phải công cụ xóa bí mật đã bị commit. Nếu lộ bí mật: thu hồi/rotate trước, báo chủ repository qua kênh riêng, phối hợp xử lý lịch sử; không đăng bí mật vào issue.

## Bám WBS và thuật ngữ

Giữ nguyên Task ID/phân công trong tài liệu người dùng cung cấp. Đề xuất ngoài phạm vi phải thảo luận, không tự tạo task hay đổi milestone. Phản ánh nhận xét giảng viên bằng mô tả quan sát: mắt nhắm, hướng đầu, mặt không được phát hiện; không dùng nhãn kết luận tâm lý hoặc gian lận.

Issue/PR không đính kèm hình người thật, MSSV, email cá nhân, token hoặc log có dữ liệu riêng tư. Tên đầy đủ/MSSV cần có trong báo cáo học phần theo WBS nhưng chưa cung cấp; bổ sung vào bản nộp có quyền truy cập phù hợp, không đoán và không tự công khai.
