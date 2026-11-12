# AI Core v1 · T07, T08 và T15

Từ thư mục gốc, dùng Python, dependencies và model Face Landmarker float16 v1 của [T03](t03-report.md). Mỗi lượt cần thư mục đầu ra mới.

```powershell
$p = ".\.venv\Scripts\python.exe"
$model = "ai-core/results/t03/face_landmarker.task"
& $p ai-core/raw_signals.py --video "duong-dan/video.avi" --model $model --output ai-core/results/raw-video --blendshapes
& $p ai-core/raw_signals.py --camera 0 --max-frames 120 --model $model --output ai-core/results/raw-webcam
```

Chạy lệnh CLI để bắt đầu và nhấn **Ctrl+C** để dừng sau thao tác đọc hoặc phân tích đang chạy. CLI đóng camera, JSONL và CSV trước khi thoát. Bỏ `--max-frames` để chạy webcam đến khi dừng. Video tự dừng ở cuối file. Dùng `--version` để xem phiên bản module. Phiên bản contract do nhóm quản lý riêng.

- `raw-signals.jsonl` ghi một bản ghi mỗi frame giải mã được hoặc mỗi lần đọc webcam thất bại, theo schema 0.1.0-draft. `sequence` bắt đầu từ 0. Với video, dùng `offset_ms` để khớp nhãn và `--video-start-utc` nếu biết thời điểm bắt đầu ghi hình. Khi bỏ tùy chọn đó, `timestamp` dùng thời điểm bắt đầu lượt đọc cộng offset, vì thời điểm ghi gốc chưa biết. Webcam đo offset bằng đồng hồ đơn điệu. Dùng `--synthetic` cho fixture được dựng. [Mẫu JSONL](../shared/examples/raw-signals.sample.jsonl)
- Khi đọc webcam thất bại, CLI ghi `quality=unavailable` với mọi phép đo là `null`, chờ 50 ms rồi thử tiếp. Sau 10 lần thất bại liên tiếp, CLI báo lỗi và giữ log đã ghi. `--max-frames` tính cả các lần đọc thất bại. Với video, CLI giữ khoảng nhảy timestamp mà bộ giải mã cung cấp và báo lỗi nếu dừng trước số frame mà container báo. Nếu container không cung cấp số frame thì lần đọc thất bại kết thúc lượt. Số frame bị bỏ qua bên trong driver hoặc bộ giải mã chỉ có thể quan sát nếu nguồn bộc lộ khoảng thời gian hoặc lỗi đọc.
- `--blendshapes` ghi thêm CSV chứa điểm `eyeBlinkLeft`, `eyeBlinkRight`, `jawOpen` để đối chiếu theo `sequence` và `offset_ms`. Các điểm này độc lập với tỷ lệ EAR/MAR. Cả hai file chỉ lưu số liệu. Event Engine sở hữu ngưỡng và luật theo thời gian.
- EAR là trung bình hai khoảng cách giữa mí trên/dưới chia khoảng cách giữa hai khóe mắt. MAR là trung bình ba khoảng cách giữa môi trong trên/dưới chia khoảng cách giữa hai khóe môi trong. Dùng tọa độ pixel 2D và trái/phải theo giải phẫu người trong hình. Các chỉ số cụ thể nằm trong `raw_signals.py`.
- Mặc định số mặt là số kết quả MediaPipe trả về, giới hạn bởi `--max-faces` (mặc định 2). Nếu có `--yunet-model`, số mặt đến từ YuNet. Presence có thể suy ra từ count dương. Phép đo mắt, miệng và pose yêu cầu đúng một bộ landmarks. Ở chế độ YuNet, cần thêm đúng một hộp mặt và tâm landmarks nằm trong hộp. Frame đọc được nhưng thiếu điều kiện ghi `quality=degraded`. Lỗi inference dừng lượt và giữ các dòng đã ghi.
- Pose là góc độ từ phần xoay của ma trận MediaPipe, với yaw quanh Y, pitch quanh X và roll quanh Z theo dấu phân rã OpenCV trên đầu vào chưa lật. Zero tương ứng với hệ mặt chuẩn của model. Kết quả roll trên ảnh xoay được kiểm tra bên dưới. Cần mẫu góc thật để xác nhận cả ba trục.

## Kiểm chứng

Chạy với model và clip T03 trên Windows, thêm clip ghép từ cùng ảnh mẫu để kiểm tra số mặt. Clip ghép gồm các đoạn 30 frame, lần lượt là frame trống, một mặt, hai bản thu nhỏ đặt cạnh nhau, một mặt giảm độ sáng xuống 18%, rồi frame trống. Bài thử hai mặt bổ sung dùng hai bản của vùng cắt ngang pixel 145–494 ở ảnh gốc, một bản lật ngang, ghép cạnh nhau ở 700 × 480.

| Phép thử | Kết quả |
| --- | --- |
| T07 · Ảnh tĩnh sau 10 frame đầu | Trên 140 frame, EAR trái 0,2075, EAR phải 0,1983 và MAR 0,2061 giữ nguyên. Các điểm blink trái/phải và jaw open trung vị lần lượt 0,2215, 0,2422 và 0,1708. |
| T08 · Xoay ảnh 15° | Roll trung vị từ 0,93° lên 15,84°. Sai lệch của độ thay đổi so với phép xoay ảnh là 0,09°. |
| T08 · Frame trống, một mặt, một mặt giảm sáng | Mỗi đoạn 30 frame khớp số mặt dự kiến. |
| T08 · Hai mặt thu nhỏ trong ảnh ghép | Model trả 0 ở cả 30 frame. Đây là một trường hợp bỏ sót đã tái hiện được. |
| T08 · Hai mặt ở kích thước lớn hơn | Model trả 2 ở cả 30 frame, pose và EAR/MAR để trống. |
| Webcam · Kiểm tra đường đọc | Xuất 30 bản ghi, cả 30 ghi 0 mặt. Lượt này chưa có nhãn để đánh giá khả năng phát hiện mặt trên webcam. |

Kiểm tra 450 bản ghi của bốn lượt với JSON Schema Draft 2020-12 và format thời gian. Thứ tự frame, offset và các cột khóa của CSV đối chiếu đều khớp.

Phép đo trên ảnh tĩnh kiểm tra độ lặp lại. Thử xoay ảnh kiểm tra roll trong mặt phẳng ảnh. Kết quả trên người thật nằm ở phần T08 bên dưới.

### T07 trên clip công khai

**Mắt.** Dùng clip Eyeblink8 số 9, `27122013_152435_cam.avi`. Xử lý 5.134 frame và ghép `.tag` theo ID frame từ 0. Có 5.060 frame được gán nhãn (ID 74–5133), 41 blink ID và 5.060/5.060 frame có đúng một mặt được phát hiện. Với từng mắt, lấy cờ đóng hoàn toàn làm mẫu dương và frame ngoài khoảng chớp làm mẫu âm. Loại frame mắt không nhìn thấy và frame trong khoảng chớp chưa đóng hoàn toàn. AUROC dùng điểm `-EAR` hoặc điểm `eyeBlink` trực tiếp.

| Mắt | Đóng / ngoài khoảng chớp | EAR trung vị đóng / ngoài khoảng chớp | AUROC EAR | AUROC blendshape |
| --- | ---: | ---: | ---: | ---: |
| Trái | 249 / 4.648 | 0,0560 / 0,2571 | 0,9997 | 0,9998 |
| Phải | 250 / 4.648 | 0,0630 / 0,2730 | 0,9990 | 0,9995 |

Kết quả đo khả năng xếp hạng frame trên một clip. Đánh giá phát hiện toàn bộ lần chớp hoặc đặt ngưỡng cần thêm clip và giao thức mức sự kiện. [Eyeblink8 và đặc tả nhãn](https://www.blinkingmatters.com/research#datasets)

**Miệng.** Dùng clip RAVDESS `02-01-01-01-01-01-01.mp4`, một người nói, 98 frame ở 29,97 FPS. Pipeline xuất MAR trên 98/98 frame. Đánh dấu thủ công frame lấy mẫu mỗi bốn frame theo hình ảnh môi và bỏ frame 24 khó phân loại. Dùng sequence bắt đầu từ 0.

- Mở miệng (10 frame) `28, 32, 36, 40, 44, 52, 56, 60, 64, 68`.
- Khép miệng (14 frame) `0, 4, 8, 12, 16, 20, 48, 72, 76, 80, 84, 88, 92, 96`.
- MAR trung vị **0,1265** khi mở và **0,0029** khi khép. `jawOpen` trung vị **0,0595** khi mở và **0,0065** khi khép. Cả hai tín hiệu xếp đúng toàn bộ 140 cặp mở/khép trong mẫu đã chọn.

Đây là kiểm tra tín hiệu trên một người và các frame dễ phân biệt. Dữ liệu gốc nằm ngoài Git. [RAVDESS, Livingstone và Russo](https://zenodo.org/records/1188976)

Cả hai lượt có 5.232 bản ghi qua kiểm tra JSON Schema và đối chiếu `sequence`/`offset_ms` với CSV. Log gốc nằm trong `ai-core/results/t07-t08/eyeblink8-09/` và `ai-core/results/t07-t08/ravdess-actor01/`.

### T08 với YuNet và phép đo sai số góc

Thử YuNet 2026may trên OpenCV 5.0.0 với ngưỡng score 0,85 và NMS 0,3. Trọng số thử có SHA-256 `ebafce4e3c118d6554634be5c27ab333b4c047a9a8c3faf1d7cf93101c22f0f0`. Model được tải cục bộ. [OpenCV Zoo YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet)

```powershell
$yu = "ai-core/results/t07-t08/face_detection_yunet_2026may.onnx"
New-Item -ItemType Directory -Force (Split-Path $yu) | Out-Null
curl.exe -fL https://media.githubusercontent.com/media/opencv/opencv_zoo/main/models/face_detection_yunet/face_detection_yunet_2026may.onnx -o $yu
& $p ai-core/raw_signals.py --video "duong-dan/video.avi" --model $model --yunet-model $yu --output ai-core/results/raw-yunet
& $p ai-core/raw_signals.py --camera 0 --max-frames 120 --model $model --yunet-model $yu --output ai-core/results/raw-yunet-webcam
```

Trên hai clip ghép đã mô tả, MediaPipe đếm đúng 150/180 frame và YuNet đếm đúng 180/180. Chênh lệch đến từ đoạn hai mặt thu nhỏ (0/30 với MediaPipe, 30/30 với YuNet). Với YuNet, cả 60 frame có đúng một mặt xuất pose. Cả 60 frame có hai mặt để trống pose. Lượt webcam xuất 20 bản ghi và cả 20 ghi 0 mặt, nên chỉ xác nhận đường đọc và xuất log. Cả 200 bản ghi tích hợp qua kiểm tra schema.

Khi có CSV tham chiếu `sequence,yaw,pitch,roll`, chuyển nhãn sang cùng hệ trục, dấu và đơn vị độ trước khi so sánh. `sequence` bắt đầu từ 0, tính theo thứ tự giải mã trong clip đã đưa vào pipeline. Script báo MAE có xét vòng 360° và độ phủ, tách frame thiếu bản ghi khỏi frame có bản ghi nhưng thiếu pose.

```powershell
& $p ai-core/evaluate_pose.py ai-core/results/raw-yunet/raw-signals.jsonl "duong-dan/pose-reference.csv"
```

Đã kiểm tra quy đổi trên bảy ma trận dựng sẵn gồm xoay ±30° theo từng trục và một trường hợp xoay kết hợp. Sai số số học tối đa dưới 0,00001°.

#### Góc đầu tương đối trên BIWI

Dùng bản RGB JPEG do fast.ai lưu trữ. Từ phần archive tải được, chỉ đọc các thành viên hoàn chỉnh. Chọn ba chuỗi có đủ ảnh ghép với file pose và có `rgb.cal`. Sắp xếp theo ID frame và lấy mỗi cặp thứ năm. Các clip đầu vào MJPG 640 × 480 được dựng từ ảnh đã chọn. FPS của clip dựng phục vụ đọc tuần tự. [Bản lưu BIWI của fast.ai](https://s3.amazonaws.com/fast-ai-imagelocal/biwi_head_pose.tgz) · [Mô tả và điều khoản BIWI](https://huggingface.co/datasets/ETHZurich/biwi_kinect_head_pose)

Chuyển ma trận pose từ camera depth sang camera RGB bằng phần xoay trong `rgb.cal`, rồi đổi cơ sở sang trục MediaPipe bằng `diag(1, -1, -1)`. So sánh chuyển động tương đối từ frame đầu của từng chuỗi. Với mỗi nguồn, tính `R_i @ R_0.T` trước khi tách Euler. Với dự đoán, dựng lại ma trận từ các góc theo thứ tự `Rz(roll) @ Ry(yaw) @ Rx(pitch)`. Bỏ frame mốc khỏi tập chấm. MAE chỉ tính ở frame có pose, còn độ phủ tính trên mọi frame tham chiếu. [Tài liệu hiệu chuẩn BIWI+](https://github.com/kuhnkeF/headposeplus#biwi-calibration)

| Chuỗi | Có pose / tham chiếu | MAE yaw | MAE pitch | MAE roll |
| --- | ---: | ---: | ---: | ---: |
| 01 | 74/99 | 2,15° | 4,80° | 2,88° |
| 06 | 59/108 | 1,95° | 2,33° | 2,34° |
| 12 | 143/146 | 2,24° | 5,56° | 3,58° |
| Tổng theo frame | **276/353 (78,2%)** | **2,15°** | **4,67°** | **3,13°** |

Phép thử này đo sai số của độ xoay so với frame mốc trên ba chuỗi. Có 77 frame thiếu pose. Kết quả không xác định sai số góc tuyệt đối hoặc hiệu năng trên toàn bộ BIWI.

#### Đếm mặt trên video thực tế

Lấy mẫu từ clip phỏng vấn của Julieta Vergara Bada (CC BY 4.0), dựng clip MJPG từ 17 frame để chạy hai detector. Gán nhãn số mặt tiền cảnh nhìn rõ trước khi đối chiếu. ID frame gốc bắt đầu từ 0. Nhãn 0 ở 150 và 175, nhãn 2 ở 75, 100 và 300, nhãn 1 ở 0, 25, 350, 375, 400, 425, 450, 475, 500, 525, 550 và 575. [Video gốc và giấy phép](https://commons.wikimedia.org/wiki/File:ENTREVISTA_A_UNA_PAREJA_EXTRANJERA.webm)

| Detector | Khớp số mặt tiền cảnh | Khớp ở frame có hai mặt tiền cảnh | Sai lệch tuyệt đối trung bình |
| --- | ---: | ---: | ---: |
| MediaPipe | 14/17 | 0/3 | 0,18 mặt |
| YuNet | 10/17 | 3/3 | 0,47 mặt |

YuNet trả số mặt cao hơn nhãn ở 7 frame. Detector đếm trên toàn ảnh còn nhãn chỉ bao gồm tiền cảnh, nên các trường hợp vượt nhãn có thể bao gồm mặt hậu cảnh. Phép thử chỉ đối chiếu số lượng, chưa xác minh từng hộp mặt. Log gốc của các lượt thử nằm trong `ai-core/results/t07-t08/`.
