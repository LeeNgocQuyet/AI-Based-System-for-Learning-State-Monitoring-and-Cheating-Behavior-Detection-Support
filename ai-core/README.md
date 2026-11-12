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

T07 và T08 có [CLI trích xuất tín hiệu mắt/miệng, hướng đầu và số mặt](raw-signals.md). Đầu ra theo [contract nháp](../shared/schemas/README.md). Ngưỡng tạo event thuộc Event Engine.
