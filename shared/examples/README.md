# Mock payload — dữ liệu tổng hợp

Mọi file JSON ở đây do người viết tự đặt, không lấy từ người thật, model hoặc video. `is_synthetic: true`; không chứa tên, tài khoản, ảnh hoặc recordings. Giá trị số chỉ minh họa cấu trúc, **không phải threshold hoặc kết quả kiểm thử/benchmark**.

| File | Mục đích |
| --- | --- |
| raw-signals.sample.json | Một mẫu đo để đối chiếu contract AI → Event Engine |
| raw-signals.unavailable.json | Mất khả năng đo; null không biến thành hành vi |
| event.sample.json | Khoảng HEAD_TURNED tổng hợp cho Backend/Frontend |
| event.browser.json | TAB_HIDDEN từ nguồn browser, không có raw-frame evidence |

Đọc file JSON bằng công cụ tùy module; chưa có mock server hoặc app để chạy. Ví dụ chỉ dùng thư viện chuẩn Python từ root:

```python
import json
from pathlib import Path
event = json.loads(Path('shared/examples/event.sample.json').read_text())
print(event['event_type'])
```

Raw sample và event sample không tạo thành chuỗi chứng minh rule kích hoạt. Huy sẽ xây timeline cho kiểm thử rules trong task hiện có sau khi thống nhất ngưỡng. UI dùng dữ liệu này phải gắn nhãn DEMO; không trộn vào dữ liệu evaluation thật.
