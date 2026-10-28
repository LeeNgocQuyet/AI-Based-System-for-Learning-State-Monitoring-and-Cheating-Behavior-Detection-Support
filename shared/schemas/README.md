# Shared schemas — DRAFT

Hai JSON Schema dùng dialect [Draft 2020-12](https://json-schema.org/draft/2020-12). “DRAFT” ở tên/version là trạng thái chưa được nhóm duyệt, độc lập với tên phiên bản chuẩn JSON Schema.

**Bắt buộc Quyết, Huy, Phúc thống nhất trước khi coi là chính thức.** Nam rà soát nhu cầu hiển thị. Producer/consumer chỉ nên dùng bản này cho mock và thảo luận.

| Schema | Đầu vào / đầu ra |
| --- | --- |
| raw-signals.schema.json | AI Core → Event Engine, mỗi phép lấy mẫu |
| event.schema.json | Event Engine/browser → Backend → Frontend, khoảng quan sát đã kết thúc |

## Quy ước đề xuất

- `schema_version = 0.1.0-draft`, `schema_status = DRAFT`; khi sửa contract phải cập nhật schema/mock/docs và review tương thích.
- `is_synthetic`: phân biệt fixture với phép đo thật; mock luôn true. Trường này là khai báo provenance, không tự chứng minh dữ liệu đã ẩn danh.
- `session_id`, `source_id`, `event_id`: mã opaque không chứa danh tính. Mock dùng tiền tố synthetic; không có tên, MSSV, email, ảnh hoặc video.
- `timestamp`: UTC RFC 3339, suffix Z; raw là thời điểm nguồn ghi nhận, event là thời điểm phát ra (không trước kết thúc interval).
- `offset_ms`, `start_offset_ms`, `end_offset_ms`, `duration_ms`: milliseconds tương đối trong cùng phiên/nguồn; không suy ra từ thời gian nhận mạng. Thời gian event là interval đã kết thúc, duration = end − start, chưa mô tả start/update realtime.
- `sequence`: số nguyên không âm, thứ tự frame tại nguồn; gap không đồng nghĩa hành vi. ID/sequence reset cần session/source mới hoặc chính sách do nhóm chốt.
- `source`: webcam/video cho raw; event có thêm browser. Browser chỉ sinh TAB_HIDDEN trong bản nháp; không sinh HEAD_TURNED.
- `face_count`: số mặt được phát hiện, null nếu không thể đo; 0 chỉ hợp lệ khi có frame đủ để detector kết luận không phát hiện mặt.
- `eye_aspect_ratio_left/right`, `mouth_aspect_ratio`: tỷ lệ không đơn vị, không phải xác suất. Công thức/landmark indices cần Quyết và Huy chốt. Không có ngưỡng hành vi trong schema.
- `head_pose_deg`: yaw/pitch/roll tính bằng độ; hệ trục, dấu và phép tính còn cần chốt. Null cả object khi không ước lượng được.
- `quality`: ok/degraded/unavailable. Unavailable yêu cầu mọi phép đo null; degraded cho phép thiếu một phần. Không biến thiếu phép đo thành zero/false.
- `severity`: hiện chỉ null vì chưa chọn chính sách. Khi nhóm chốt enum/mapping phải cập nhật version; không dùng để kết luận mức gian lận.
- `evidence`: tham chiếu sequence của raw cùng session/source; với browser để null. Không nhúng raw video hay thông tin người thật. Mapping nhiều mặt và chọn target chưa được giải quyết bởi schema này.

`additionalProperties: false` giúp phát hiện trường lệch contract; chưa phải chính sách migration v1. Validator CI bật kiểm tra format và kiểm tra quan hệ thời gian ở script vì JSON Schema không tự so sánh các trường. Hợp lệ schema không có nghĩa rule/AI đúng hoặc data đã được phép thu.
