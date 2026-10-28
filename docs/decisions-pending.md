# Các quyết định cần nhóm xác nhận

Không có quyết định nào dưới đây được coi là đã phê duyệt chỉ vì xuất hiện trong scaffold.

| Quyết định | Người cần tham gia | WBS |
| --- | --- | --- |
| MVP, taxonomy, MOUTH_OPEN so với yawning, nội dung trung tính | Cả nhóm | T01/T04/T05 |
| Raw/event fields, đơn vị EAR/MAR, hệ trục pose, null, version, source/clock | Quyết + Huy + Phúc; Nam phản hồi | T02/T15 |
| Onset/offset, thresholds, smoothing/debounce, rule lifecycle | Huy + Quyết | T04/T09/T16 |
| Severity và chính sách hiển thị/cooldown học/thi | Huy + Phúc + Nam | T02/T17/T25 |
| Nơi chạy AI, truyền frame, đồng bộ nguồn webcam/video | Quyết + Phúc + Nam | T03/T15/T19 |
| Framework backend/frontend, DB, API/WS/OpenAPI, retry/replay | Phúc + Nam, cả nhóm thống nhất tích hợp | T02/T11/T12/T17 |
| Quyền theo phiên, cấp tài khoản giảng viên, dữ liệu lưu | Phúc + cả nhóm | T11/T24 |
| Pause, đã xem, export; phone detection có đủ điều kiện đưa vào MVP | Cả nhóm | T01/T05/T25 |
| Đồng thuận, nơi lưu video, ai truy cập, retention, lịch xóa | Cả nhóm + giảng viên theo quy trình trường | T10/T23/T27 |
| Nhãn, split, event matching, tolerance, đơn vị metrics | Huy + Quyết | T04/T20/T22 |
| Pilot 3–5 và study mục tiêu 20–24: tuyển mẫu, A/B, lịch cảnh báo, rubric, phân tích | Huy + Nam; cả nhóm/giảng viên duyệt | T06/T23/T27/T28 |
| Mốc lịch WBS “25/10 - 1/10”; tên đầy đủ/MSSV trong bản nộp | Cả nhóm | T01/T32 |
| GitHub handles của Huy/Phúc/Nam cho CODEOWNERS; ruleset; license | Chủ repo + cả nhóm | Quy trình phối hợp, không tạo task WBS mới |

Khi chốt, cập nhật tài liệu bằng PR gắn task hiện có và ghi người/ngày xác nhận. Không tự chuyển schema sang v1 chính thức hoặc coi T02/T06 đã hoàn thành.
