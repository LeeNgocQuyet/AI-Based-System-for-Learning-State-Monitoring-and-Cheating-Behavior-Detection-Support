# frontend

**Phụ trách:** Nam. **WBS hiện có:** T05, T13, T14, T18, T25, T31.

## Phạm vi và trách nhiệm

UI/UX người học và giảng viên, quyền camera, trạng thái kết nối, cảnh báo trung tính; prototype A/B với Huy.

## Đầu vào

Event mock hoặc contract API/WebSocket khi nhóm chốt; trạng thái phiên và quyền từ backend.

## Đầu ra

Hiển thị S01–S12, thao tác phiên và tín hiệu browser theo contract tương lai; không tự cấp quyền bằng UI.

## Phát triển ban đầu

Đọc `docs/product-context.md` và protocol HCI; tải các file JSON trong shared/examples vào công cụ prototype tùy chọn. Chưa chọn framework/build tool và chưa có ứng dụng chạy. Không bật camera ngay khi login; không hiển thị mock lẫn với dữ liệu thật.

Từ root, chạy kiểm tra nền tảng theo [README](../README.md). Xem [mock](../shared/examples/README.md) và [quy trình PR](../CONTRIBUTING.md). Schema còn DRAFT, cần Quyết + Huy + Phúc xác nhận. Module hiện chỉ có tài liệu; không có test ứng dụng để chạy.
