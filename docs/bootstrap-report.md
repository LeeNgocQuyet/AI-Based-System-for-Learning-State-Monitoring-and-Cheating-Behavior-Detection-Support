# Báo cáo khởi tạo nền tảng

## Phạm vi

Bộ nền tảng theo yêu cầu người dùng, tham chiếu WBS T01/T02/T04/T06 mà không tạo task mới hoặc cập nhật trạng thái WBS. Không có triển khai AI inference, engine, API, DB hoặc UI. Không chọn framework. Không có dữ liệu người thật trong fixtures.

Kiểm tra ban đầu: workspace chưa có source; `.git` không phải repository hợp lệ và chỉ đọc. GitHub repository được chỉ định đang public và rỗng. Không ghi đè dữ liệu sẵn có, không thay visibility/quyền hay mời thành viên.

## Danh sách file

- `.editorconfig`
- `.github/ISSUE_TEMPLATE/bug.md`
- `.github/ISSUE_TEMPLATE/feature.md`
- `.github/pull_request_template.md`
- `.github/workflows/ci.yml`
- `.gitignore`
- `CONTRIBUTING.md`
- `README.md`
- `ai-core/README.md`
- `backend/README.md`
- `docs/api/README.md`
- `docs/architecture/README.md`
- `docs/architecture/event-taxonomy.md`
- `docs/bootstrap-report.md`
- `docs/data-governance.md`
- `docs/decisions-pending.md`
- `docs/evaluation/README.md`
- `docs/evaluation/hci-protocol.md`
- `docs/product-context.md`
- `docs/repository-governance.md`
- `event-engine/README.md`
- `frontend/README.md`
- `scripts/README.md`
- `scripts/foundation-files.json`
- `scripts/requirements-ci.txt`
- `scripts/validate_repository.py`
- `shared/examples/README.md`
- `shared/examples/event.browser.json`
- `shared/examples/event.sample.json`
- `shared/examples/raw-signals.sample.json`
- `shared/examples/raw-signals.unavailable.json`
- `shared/schemas/README.md`
- `shared/schemas/event.schema.json`
- `shared/schemas/raw-signals.schema.json`

## Kiểm tra và giới hạn

Lệnh tái lập: `python scripts/validate_repository.py` sau khi cài `scripts/requirements-ci.txt`. Check chỉ đánh giá file, YAML, JSON Schema, fixtures tổng hợp và khả năng từ chối payload sai; không phải kiểm thử hành vi ứng dụng. Trạng thái chạy thực tế và bàn giao GitHub được ghi trong báo cáo cuối của lần thực hiện, không tự tuyên bố CI remote đã đạt.

Các quyết định cần xác nhận nằm ở [decisions-pending.md](decisions-pending.md). `.env.example` chưa cần vì chưa có runtime ứng dụng; chưa tạo CODEOWNERS vì thiếu tài khoản, chưa chọn license. Ruleset chỉ mới được đề xuất.
