# **Đặc tả sự kiện & Hướng dẫn gán nhãn (Task T04)**

## **Nhóm 3 (HCI)**

---

# **1\. Đặc tả quy tắc sự kiện (Event Rule Spec v0)**

Tài liệu này quy định các ngưỡng (threshold), điểm kích hoạt (onset), và điểm kết thúc (offset) dựa trên các tín hiệu giả lập (mock signals) nhằm xác định chính xác các trạng thái hành vi của người học.

| Tên sự kiện | Tín hiệu giả lập | Ngưỡng (Threshold) | Điểm kích hoạt (Onset) | Điểm kết thúc (Offset) |
| :---- | :---- | :---- | :---- | :---- |
| **Nhắm mắt kéo dài***(Nghi ngờ buồn ngủ)* | `eye_aspect_ratio`*(EAR)* | `EAR < 0.2` | Duy trì liên tục trong **3 giây***(Loại trừ chớp mắt tự nhiên)* | `EAR > 0.25` duy trì ổn định ít nhất **2 giây** |
| **Quay đầu / Rời mắt***(Giảm tập trung / Gian lận)* | `head_yaw_angle`*(Góc quay ngang)* | `|head_yaw_angle| > 30°` | Vượt ngưỡng liên tục trong **5 giây***(Loại trừ quan sát nhanh xung quanh)* | `|head_yaw_angle| < 15°` duy trì trong **2 giây** |
| **Bất thường khuôn mặt***(Vắng mặt / Nhiều người)* | `face_count` | `face_count == 0`hoặc `face_count > 1` | Duy trì liên tục trong **2.5 giây***(Loại trừ giật lag camera / che mặt)* | `face_count == 1` duy trì ổn định trong **2 giây** |

---

# **2\. Hướng dẫn gán nhãn (Annotation Guide)**

Hướng dẫn dành cho các thành viên thực hiện phân loại và chuẩn hóa dữ liệu kiểm thử hệ thống:

## **2.1. Tiêu chí đúng (True Positive)**

Hành vi vi phạm được ghi nhận là **Dương tính thật** khi thỏa mãn đồng thời hai điều kiện:

* **Đặc điểm vật lý:** Tín hiệu đầu vào đạt hoặc vượt ngưỡng (threshold) quy định.  
* **Thời gian duy trì:** Thời lượng diễn ra hành vi đạt tối thiểu khoảng thời gian kích hoạt (onset).

## **2.2. Các tình huống ngoại lệ cần loại trừ (False Positive tiềm năng)**

Cần lưu ý phân biệt các tình huống nhiễu thực tế để tránh gán nhãn sai cho hệ thống:

* **Trường hợp cúi đầu nháp bài:**  
  * *Hiện tượng:* Người học cúi nhìn xuống bàn để tính toán hoặc ghi chép. Hệ thống có thể ghi nhận `EAR` giảm thấp và góc cúi đầu tăng.  
  * *Quy tắc gán nhãn:* Đánh dấu là **"Tập trung học / Bình thường"**, không gán nhãn "Buồn ngủ".  
* **Trường hợp người xuất hiện phía sau (Người qua đường):**  
  * *Hiện tượng:* Phụ huynh hoặc người thân ngẫu nhiên đi ngang qua khung hình trong khoảng 1–2 giây khiến `face_count` \= 2\.  
  * *Quy tắc gán nhãn:* Do chưa đủ thời gian kích hoạt (onset \= 2.5s), sự kiện không được kích hoạt Cảnh báo. Đánh dấu là **"Bình thường"**.

