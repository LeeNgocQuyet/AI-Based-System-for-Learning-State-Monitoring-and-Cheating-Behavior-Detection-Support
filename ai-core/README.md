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

T15 đóng gói các phép đo T07 và T08 thành [AI Core v1 và hướng dẫn start/stop](raw-signals.md). Module xuất JSONL theo [contract nháp](../shared/schemas/README.md). Xem [mẫu đầu ra](../shared/examples/raw-signals.sample.jsonl). Ngưỡng tạo event thuộc Event Engine.
