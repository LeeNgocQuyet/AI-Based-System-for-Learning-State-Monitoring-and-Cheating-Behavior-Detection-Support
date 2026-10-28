# Công cụ nền tảng

`validate_repository.py` kiểm tra file bắt buộc, UTF-8/newline, YAML workflow/template, JSON Schema và mọi mock JSON. Có kiểm tra quan hệ thời gian/sequence, trường synthetic và một số payload không hợp lệ để bảo đảm validator thực sự từ chối sai contract.

Chạy từ root theo README; `requirements-ci.txt` chỉ dành cho công cụ kiểm tra, không chọn dependencies/framework cho ứng dụng. Script dùng đường dẫn theo vị trí chính nó nên có thể gọi từ thư mục khác.

CI không chạy AI, Event Engine, Backend hoặc Frontend khi chưa có source; không có job giả báo pass cho những module đó. Check đạt chỉ chứng minh scaffold/contract nhất quán, không chứng minh inference đúng, hiệu năng tốt hoặc nghiên cứu đã diễn ra.
