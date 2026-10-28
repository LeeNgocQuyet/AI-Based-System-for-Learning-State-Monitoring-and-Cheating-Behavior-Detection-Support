# event-engine

**Phụ trách:** Huy. **WBS hiện có:** T04, T09, T16; evaluation/HCI T06, T10, T20, T22, T23, T27, T28.

## Phạm vi và trách nhiệm

Phân tích raw signals theo thời gian; định nghĩa onset/offset, debounce, xử lý thiếu tín hiệu; duy trì evaluation/HCI.

## Đầu vào

Raw signals từ AI Core hoặc mock tổng hợp.

## Đầu ra

Events theo `shared/schemas/event.schema.json`, kèm khoảng thời gian và bằng chứng tham chiếu.

## Phát triển ban đầu

Đọc fixtures và taxonomy; thiết kế rule spec trong T04 trước khi hiện thực T09. Ngưỡng, smoothing và cooldown chưa chốt. Huy sở hữu debounce/rule lifecycle; Phúc sở hữu giới hạn tần suất hiển thị theo T17. Không coi mất landmarks là mắt nhắm hoặc người học rời chỗ.

Từ root, chạy kiểm tra nền tảng theo [README](../README.md). Xem [mock](../shared/examples/README.md) và [quy trình PR](../CONTRIBUTING.md). Schema còn DRAFT, cần Quyết + Huy + Phúc xác nhận. Module hiện chỉ có tài liệu; không có test ứng dụng để chạy.
