# Đề xuất quản trị GitHub

Repository được người dùng chỉ định: `LeeNgocQuyet/AI-Based-System-for-Learning-State-Monitoring-and-Cheating-Behavior-Detection-Support`. Kiểm tra ban đầu ngày 28/10/2026: public, default branch khai báo main, chưa có commit. Giữ nguyên visibility và quyền thành viên. Tài liệu này chỉ là đề xuất, không có nghĩa ruleset đã được bật.

## Bảo vệ main cho nhóm bốn người

Đề xuất ruleset active nhắm `main`: bắt buộc PR, ít nhất 1 approval từ người khác, dismiss approval cũ khi có thay đổi mới, resolve review conversations, required check `Repository foundation`, chặn force push và xóa nhánh. Chọn GitHub Actions làm nguồn check nếu có thể. Không đặt merge queue hoặc deployment approval khi chưa có nhu cầu.

Sau CI chạy thành công lần đầu, chủ repo chọn đúng check để tránh rule yêu cầu check chưa tồn tại. Đề xuất nhánh phải cập nhật với main trước merge; review lại nếu xung đột. Chỉ cấu hình bypass khi nhóm có lý do rõ và ghi quy trình; không dùng bypass cho công việc thường ngày. Mỗi PR contract vẫn cần Quyết/Huy/Phúc xác nhận ngữ nghĩa theo CONTRIBUTING.

Chưa tạo CODEOWNERS do thiếu GitHub handles của ba thành viên; không đoán tài khoản hoặc mời thành viên. Không tự chọn license thay nhóm.

## Repository rỗng và lần khởi tạo

PR cần nhánh base có commit. Người dùng đã chấp thuận ngoại lệ khởi tạo một lần: tạo duy nhất file `.gitkeep` rỗng trên main qua kết nối GitHub, sau đó đưa toàn bộ scaffold lên `feature/T01-repository-foundation` và mở Draft PR vào main. Git CLI chưa có xác thực để push commit rỗng và connector không hỗ trợ tạo commit gốc rỗng. Ngoại lệ này chỉ áp dụng cho file mốc ban đầu; toàn bộ tài liệu, schema, mock và CI vẫn đi qua PR.

Đối chiếu hướng dẫn chính thức: [GitHub protected branches](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [status checks](https://docs.github.com/en/pull-requests/reference/status-checks). Tính khả dụng phụ thuộc gói/tầm nhìn repo; kiểm tra lại trước áp dụng nếu thay visibility.
