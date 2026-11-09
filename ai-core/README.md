# ai-core

**Phụ trách:** Quyết. **WBS hiện có:** T03, T07, T08, T15, T21, T29.

## Phạm vi và trách nhiệm

MediaPipe/OpenCV và mô hình pretrained; trích xuất đặc trưng mắt, miệng, khuôn mặt, hướng đầu; ghi điều kiện benchmark.

## Đầu vào

Webcam hoặc video được phép sử dụng; cấu hình extraction sẽ được chốt.

## Đầu ra

Raw signals theo `shared/schemas/raw-signals.schema.json`, có thời gian, số thứ tự và tình trạng tín hiệu.

## Phát triển ban đầu

T03 có PoC MediaPipe Face Landmarker chạy cục bộ bằng OpenCV. Xem [khảo sát, cách chạy và benchmark T03](t03-report.md).

T07 phụ trách tín hiệu mắt/miệng. T08 phụ trách head pose và phát hiện/đếm mặt. Cả hai dùng [contract nháp và dữ liệu mẫu](../shared/examples/README.md) làm điểm xuất phát. Quyết, Huy và Phúc cần xác nhận schema, công thức EAR/MAR, hệ trục head pose, nguồn thời gian và chất lượng tín hiệu. Ngưỡng tạo event thuộc Event Engine.
