# backend

**Phụ trách:** Phúc. **WBS hiện có:** T02, T11, T12, T17, T24, T30.

## Phạm vi và trách nhiệm

Contract, xác thực và quyền truy cập, lưu sự kiện, API/WebSocket, tổng hợp phiên; chưa chọn framework hay DB.

## Đầu vào

Events từ Event Engine; sự kiện browser từ nguồn riêng sau khi chốt contract; yêu cầu phiên từ frontend.

## Đầu ra

Event API/WebSocket và báo cáo theo quyền truy cập, thiết kế tại `docs/api/README.md`.

## Phát triển ban đầu

Dùng event mock để thảo luận API độc lập AI. Đọc data-governance trước khi chốt RBAC. Chưa có server, migration hay API chạy được; chưa tạo credentials hoặc `.env`.

Từ root, chạy kiểm tra nền tảng theo [README](../README.md). Xem [mock](../shared/examples/README.md) và [quy trình PR](../CONTRIBUTING.md). Schema còn DRAFT, cần Quyết + Huy + Phúc xác nhận. Module hiện chỉ có tài liệu; không có test ứng dụng để chạy.
