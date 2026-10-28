# ai-core

**Phụ trách:** Quyết. **WBS hiện có:** T03, T07, T08, T15, T21, T29.

## Phạm vi và trách nhiệm

MediaPipe/OpenCV và mô hình pretrained; trích xuất đặc trưng mắt, miệng, khuôn mặt, hướng đầu; ghi điều kiện benchmark.

## Đầu vào

Webcam hoặc video được phép sử dụng; cấu hình extraction sẽ được chốt.

## Đầu ra

Raw signals theo `shared/schemas/raw-signals.schema.json`, có thời gian, số thứ tự và tình trạng tín hiệu.

## Phát triển ban đầu

Đọc contract và mock raw-signals trước; đề xuất định nghĩa EAR/MAR, hệ trục head pose, nguồn thời gian và chất lượng tín hiệu. Chưa có CLI, dependencies hay inference để chạy. Không đặt ngưỡng tạo event ở module này.

Từ root, chạy kiểm tra nền tảng theo [README](../README.md). Xem [mock](../shared/examples/README.md) và [quy trình PR](../CONTRIBUTING.md). Schema còn DRAFT, cần Quyết + Huy + Phúc xác nhận. Module hiện chỉ có tài liệu; không có test ứng dụng để chạy.
