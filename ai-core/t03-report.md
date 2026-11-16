# T03 · Khảo sát công nghệ và PoC webcam/video

Chọn **MediaPipe Tasks Face Landmarker (pretrained float16 v1)** để lấy landmarks và ma trận hướng mặt. Dùng **OpenCV** để đọc video/webcam, đổi BGR sang RGB, vẽ overlay và xuất demo. T03 thử trên một mặt mỗi frame, dùng chế độ VIDEO cho cả hai nguồn để xử lý tuần tự. [MediaPipe Face Landmarker](https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/FaceLandmarkerOptions) · [OpenCV VideoCapture](https://docs.opencv.org/4.10.0/d4/d15/group__videoio__flags__base.html)

| Phương án | Kết quả khảo sát |
| --- | --- |
| MediaPipe Face Landmarker + OpenCV | PoC thu được 478 landmarks trên các frame có mặt của clip thử. Có đủ điểm quanh mắt, môi, viền mặt và có ma trận biến đổi mặt để thử góc xoay. |
| OpenCV YuNet (`FaceDetectorYN`) | Trả bounding box và 5 điểm trên mặt. Có thể xem xét cho phần phát hiện mặt T08. Số điểm chưa đủ để quan sát đường viền mí và môi trong T03. Đối chiếu này dựa trên đầu ra được tài liệu hóa. |

[Kết quả MediaPipe Face Landmarker](https://ai.google.dev/edge/api/mediapipe/python/mp/tasks/vision/FaceLandmarkerResult) · [Tài liệu OpenCV YuNet](https://docs.opencv.org/5.0/tutorials/dnn/dnn_face/dnn_face.html)

## Chạy lại từ thư mục gốc

Ví dụ PowerShell với Python 3.14.7 trên Windows. Dùng một đường dẫn đầu ra mới cho mỗi lần chạy.

```powershell
python -m venv .venv
$p = ".\.venv\Scripts\python.exe"
& $p -m pip install -r ai-core/requirements-t03.txt

$work = "ai-core/results/t03-repro"
New-Item -ItemType Directory -Force $work | Out-Null
curl.exe -fL https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task -o "$work/face_landmarker.task"
curl.exe -fL https://storage.googleapis.com/mediapipe-assets/portrait.jpg -o "$work/portrait.jpg"

& $p ai-core/t03_fixture.py "$work/portrait.jpg" "$work/fixture.avi"
& $p ai-core/t03_poc.py --video "$work/fixture.avi" --model "$work/face_landmarker.task" --output "$work/demo" --save-video
& $p ai-core/t03_poc.py --video "$work/fixture.avi" --model "$work/face_landmarker.task" --output "$work/static" --max-frames 150
& $p ai-core/t03_poc.py --camera 0 --model "$work/face_landmarker.task" --output "$work/webcam" --max-frames 60
```

Có thể thay clip bằng video bạn được phép sử dụng. Dùng `--preview` để xem trực tiếp và nhấn `q` hoặc Esc để dừng. Script mặc định chỉ xuất log số liệu. Chỉ thêm `--save-video` khi có quyền ghi/lưu hình ảnh. Tùy chọn này cần nguồn báo được FPS để ghi MP4. Overlay dùng màu xanh lá cho mắt, cam cho miệng và xanh lam cho viền mặt. [Quản lý dữ liệu dự án](../docs/data-governance.md)

Mỗi lần chạy tạo `frames.csv` và `benchmark.json`, kèm `overlay.mp4` khi bật ghi. Timestamp video ưu tiên vị trí do OpenCV cung cấp, có fallback theo FPS danh định. Webcam dùng đồng hồ đơn điệu của tiến trình. CSV là log chẩn đoán T03. Cột `landmark_count` đếm số điểm trên mặt đang theo dõi.

## Kết quả chạy cục bộ

Ngày 09/11/2026, Windows 10, AMD Ryzen 7 3750H (8 luồng logic), CPU XNNPACK, Python 3.14.7, MediaPipe 1.2.2 và OpenCV 5.0.0. Model SHA-256 `64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff`. Đầu vào 640 × 480. Clip 30 FPS, 240 frame, ghép từ ảnh mẫu Google MediaPipe với 150 frame ảnh gốc, 30 frame trống và 60 frame xoay ảnh 15°. Webcam index 0 chạy qua DirectShow, trong lượt thử ngắn với ánh sáng phòng chưa chuẩn hóa.

| Lượt chạy | Frame đo sau 10 frame khởi động | Frame có landmarks / có pose | FPS inference | FPS pipeline | Inference p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Video demo, có ghi overlay | 230 | 200 / 200 | 66,63 | 50,32 | 18,33 ms |
| Video, đoạn tĩnh, chỉ log | 140 | 140 / 140 | 58,98 | 51,90 | 19,17 ms |
| Webcam, chỉ log | 50 | 22 / 22 | 67,68 | 14,90 | 18,65 ms |

- **FPS inference** đo lời gọi `detect_for_video`. **FPS pipeline** bao gồm đọc frame, chuyển màu, inference, tính pose và ghi overlay nếu bật. Khâu mở nguồn, tải model và ghi CSV/JSON cuối lượt nằm ngoài phép đo. FPS webcam bao gồm thời gian chờ đọc camera.
- **Độ ổn định landmarks** đo RMS dịch chuyển 2D theo pixel qua mỗi cặp frame liền kề có mặt. Trên 139 cặp đoạn ảnh tĩnh, median là **0,00068 px**, p95 là **0,00236 px**. Đây là độ lặp lại trên cùng ảnh. Chuyển động thật, ánh sáng và sai số vị trí tuyệt đối cần mẫu đánh giá riêng.
- **Head pose sơ bộ** tách góc X/Y/Z từ phần xoay của ma trận biến đổi mặt. Median góc Z là **0,22°** trên ảnh gốc và **15,54°** trên ảnh xoay. Kiểm tra này xác nhận phản ứng với xoay trong mặt phẳng ảnh. T08 sẽ chốt quy ước trục và đo sai số góc đầu thật.
- **Kiểm tra đầu ra** đọc lại đủ 240 frame overlay, kiểm tra kích thước và FPS, đối chiếu thứ tự và timestamp tăng ở cả ba CSV. Clip có 478 điểm ở các đoạn có mặt, 30 frame trống có 0 điểm và góc để trống. Webcam có 22/50 frame phát hiện sau khởi động. Lượt webcam chỉ xác nhận đường đọc và inference, vì trạng thái có mặt theo từng frame chưa được gán nhãn.

Demo và log gốc của lượt đo nằm trong thư mục cục bộ `ai-core/results/t03/`, được Git bỏ qua. Báo cáo này giữ số đo tổng hợp và lệnh tái tạo. T07 tiếp tục với tín hiệu mắt/miệng. T08 tiếp tục với head pose, face count và đánh giá điều kiện khó.
