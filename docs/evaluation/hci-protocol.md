# Protocol HCI — DRAFT (T06/T23/T27/T28)

Huy chủ trì, Nam rà soát khả năng thực hiện UI. Đây là kế hoạch để nhóm duyệt, chưa tuyển người hoặc chạy thử. **Pilot 3–5 người và mục tiêu user study 20–24 người** lấy từ WBS, không phải cỡ mẫu đã đạt hoặc kết quả power analysis.

## Mục tiêu

Đánh giá người dùng cảm nhận cảnh báo có công bằng, có quyền kiểm soát, gây phiền đến đâu và có hiểu giới hạn ý nghĩa cảnh báo hay không. Không dùng study UI này để tuyên bố độ chính xác AI hoặc phát hiện gian lận.

## Người tham gia và đồng thuận — đề xuất

Tuyển người học tự nguyện phù hợp bối cảnh, không gây áp lực điểm số. Thống nhất tiêu chí tuyển/loại và yêu cầu của trường trước khi tuyển; không tự tuyển người chưa thành niên. Phân biệt dữ liệu pilot với study chính; đề xuất không gộp pilot sau khi đã sửa prototype. Nếu không đạt 20–24, báo số thực tế và giới hạn, không bổ sung câu trả lời giả.

Trước buổi thử: giải thích đây là prototype có cảnh báo dựng sẵn, không đánh giá đạo đức/năng lực; nêu quyền từ chối, nghỉ/dừng, dữ liệu lưu và thời hạn xóa. Ghi âm/quay màn hình/webcam cần đồng thuận riêng. Mặc định dùng nội dung tổng hợp và không ghi webcam người tham gia.

## Điều kiện A/B — đề xuất cần Nam và Huy chốt

A: cảnh báo trung tính, mô tả tín hiệu quan sát được.
B: cùng cảnh báo, thêm giải thích giới hạn và gợi ý khắc phục, cùng mức độ nổi bật.

Hai biến thể có cùng quyền dừng/kết thúc, vị trí hiển thị, nhiệm vụ, lịch cảnh báo và giới hạn tần suất. Khác biệt là gói nội dung giải thích; không diễn giải kết quả là tác động riêng của từng thành phần. Không dùng nội dung buộc tội ở A để làm B có vẻ tốt hơn.

Thiết kế trong người, counterbalanced AB/BA theo WBS; phân bổ số người gần bằng nhau, ghi thứ tự thực tế. Dùng hai bộ bài đọc/câu hỏi tương đương về độ khó, hoán đổi giữa điều kiện để giảm hiệu ứng học. Giữ thiết bị, hướng dẫn và thời điểm cảnh báo tương đương. Kịch bản tổng hợp giống nhau cho hai điều kiện; không để model realtime tạo số lượng cảnh báo khác nhau trong so sánh UI.

## Trình tự một buổi — thời lượng đề xuất, chưa chốt

1. Giới thiệu, đồng thuận, mã nghiên cứu: khoảng 5 phút.
2. Hướng dẫn và task làm quen không tính kết quả: khoảng 3 phút.
3. Điều kiện đầu: khoảng 8 phút làm bài đọc/câu hỏi trên prototype. Gặp các tình huống dựng sẵn: không phát hiện mặt, hướng đầu thay đổi, trang không hiển thị; luôn ghi nhãn mô phỏng.
4. Hoàn thành bảng hỏi và câu hỏi comprehension không có trợ giúp: khoảng 4 phút.
5. Nghỉ khoảng 2 phút rồi thực hiện điều kiện còn lại với cùng trình tự.
6. Phỏng vấn so sánh và debrief: khoảng 5 phút; giải thích lại mọi hiểu nhầm.

Pilot 3–5 người kiểm tra thời lượng, độ rõ task, nội dung cảnh báo, câu hỏi và thao tác lỗi. Huy ghi thay đổi, Nam sửa prototype; freeze giao diện/protocol trước study chính (đối chiếu T26). Thời lượng và script cảnh báo cụ thể được chốt sau pilot; đây không phải ngưỡng nhận dạng hành vi.

## Task quan sát

- Đọc giải thích trước phiên, tìm quyền camera và cách kết thúc. Nếu dùng webcam thật phải xin quyền riêng; prototype có thể mô phỏng camera.
- Hoàn thành bài đọc/câu hỏi trong khi nhận cảnh báo theo lịch cố định.
- Mở chi tiết một cảnh báo, giải thích bằng lời điều đã được ghi nhận và điều không thể kết luận.
- Tìm cách khắc phục/lấy lại kiểm soát; thực hiện dừng/kết thúc. Chỉ đưa pause vào task nếu MVP đã chốt và cả A/B đều có.
- Mở tóm tắt và diễn giải số sự kiện mà không gán nhãn gian lận.

Luồng giảng viên cần walkthrough riêng theo T05/T18; không coi ý kiến của người học đóng vai giảng viên là bằng chứng đại diện cho giảng viên thật. Phạm vi tuyển giảng viên vẫn cần xác nhận, không tự tăng WBS/cỡ mẫu.

## Bảng hỏi sau mỗi điều kiện — DRAFT

Thang 1–5: hoàn toàn không đồng ý → hoàn toàn đồng ý; có lựa chọn không áp dụng. Đây là item dự án tự soạn, không tuyên bố là thang đã được kiểm định.

| Nhóm đo | Item đề xuất |
| --- | --- |
| Perceived fairness | Cảnh báo mô tả tình huống mà không phán xét tôi. |
| Perceived fairness | Cách diễn đạt thừa nhận hệ thống có thể nhận định sai tín hiệu. |
| Perceived control | Tôi biết cách dừng hoặc kết thúc việc giám sát. |
| Perceived control | Tôi biết có thể làm gì khi cảnh báo không phù hợp. |
| Annoyance | Cảnh báo làm gián đoạn việc hoàn thành nhiệm vụ. |
| Annoyance | Tần suất hoặc cách trình bày cảnh báo khiến tôi khó chịu. |

Comprehension đo bằng trả lời mở, không chỉ tự đánh giá: (1) “Không phát hiện mặt” có chứng minh rời chỗ không, vì sao? (2) TAB_HIDDEN nói gì và không nói gì? (3) Nhắm mắt/hướng đầu có đủ để kết luận gian lận/giảm tập trung không? (4) Khi cảnh báo không phù hợp, bạn có thể làm gì?

Rubric dự kiến mỗi câu 0–2: 0 = diễn giải sai/không biết; 1 = đúng một phần; 2 = nêu đúng giới hạn hoặc hành động có trong prototype. Chốt đáp án chuẩn trước study; ví dụ câu 1 phải nêu khả năng do ánh sáng/góc camera, câu 2 không xác định nội dung trang khác, câu 3 không đủ chứng minh, câu 4 khớp controls thực tế. Hai người chấm một phần câu trả lời, thống nhất cách giải quyết bất đồng.

## Ghi dữ liệu và phân tích

Lưu mã nghiên cứu, thứ tự AB/BA, điều kiện, phiên bản prototype, task hoàn thành, thời gian/lỗi, câu trả lời và ghi chú đã loại danh tính. Không lưu tên/email vào bảng phân tích; lưu consent riêng ngoài Git. Hỏi cuối buổi: cảnh báo nào gây hiểu nhầm, khi nào thấy thiếu công bằng, muốn kiểm soát điều gì?

Báo số tham gia thực tế, bỏ dở, missing và lý do loại theo tiêu chí định trước. So sánh trong người A/B cho từng thước đo; báo phân bố/median và chênh lệch ghép cặp, không tự gộp fairness/control/annoyance thành “điểm chất lượng”. Kiểm tra ảnh hưởng thứ tự AB/BA. Quyết định phép kiểm định/ước lượng bất định trước phân tích theo mẫu thực có; không hứa có ý nghĩa thống kê.

Trình bày giới hạn mẫu thuận tiện, hiệu ứng học, prototype/cảnh báo mô phỏng và bối cảnh thử ngắn. Không suy diễn nhân quả rộng hoặc đánh đồng perceived fairness với kiểm định công bằng thuật toán. Không báo dữ liệu giả lập là kết quả nghiên cứu.
