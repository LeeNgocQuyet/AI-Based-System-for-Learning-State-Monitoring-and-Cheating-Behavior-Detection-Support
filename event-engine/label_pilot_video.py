import json
import sys
from pathlib import Path
import cv2

EVENT_KEYS = {
    ord("1"): ("EYES_CLOSED", "positive"),
    ord("2"): ("MOUTH_OPEN", "positive"),
    ord("3"): ("HEAD_TURNED", "positive"),
    ord("4"): ("FACE_NOT_DETECTED", "positive"),
    ord("5"): ("MULTIPLE_FACES", "positive"),
    ord("6"): ("NEG_TALKING", "hard_negative"),
    ord("7"): ("NEG_LOOKING_DOWN", "hard_negative"),
    ord("8"): ("NEG_LOW_LIGHT", "hard_negative"),
}


def main():
    if len(sys.argv) < 2:
        print("Cach dung: python event-engine/label_pilot_video.py <duong_dan_video.mp4>")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        print(f"Khong mo duoc video: {video_path}")
        sys.exit(1)

    active = {}  # key_code -> start_ms
    positive_events = []
    negative_segments = []
    last_ms = 0
    paused = False

    print("=== HUONG DAN BAM PHIM GAN NHAN ===")
    print("[1] EYES_CLOSED   [2] MOUTH_OPEN        [3] HEAD_TURNED")
    print("[4] FACE_MISSING  [5] MULTIPLE_FACES")
    print("[6] Am tinh: Noi chuyen  [7] Am tinh: Cui dau  [8] Am tinh: Anh sang yeu")
    print("[Space] Tam dung/Tiep tuc   [Q] Luu file JSON va thoat")

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break
            cur_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
            last_ms = max(last_ms, cur_ms)

            display = frame.copy()
            cv2.putText(
                display,
                f"Time: {last_ms} ms ({last_ms/1000:.1f}s) | Active: {[EVENT_KEYS[k][0] for k in active]}",
                (15, 35),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                (0, 255, 0),
                2,
            )
            cv2.imshow("Pilot Video Annotator (T10)", display)

        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            break
        elif key == ord(" "):
            paused = not paused
        elif key in EVENT_KEYS:
            label_name, category = EVENT_KEYS[key]
            if key not in active:
                active[key] = last_ms
                print(f"[BAT DAU]  {label_name} tai {last_ms} ms")
            else:
                start_ms = active.pop(key)
                record = {
                    "event_type": label_name,
                    "start_offset_ms": start_ms,
                    "end_offset_ms": last_ms,
                    "duration_ms": max(0, last_ms - start_ms),
                }
                if category == "positive":
                    positive_events.append(record)
                else:
                    negative_segments.append(record)
                print(f"[KET THUC] {label_name}: {start_ms} -> {last_ms} ms")

    # Dong cac nhan con dang mo neu het video
    for key, start_ms in active.items():
        label_name, category = EVENT_KEYS[key]
        record = {
            "event_type": label_name,
            "start_offset_ms": start_ms,
            "end_offset_ms": last_ms,
            "duration_ms": max(0, last_ms - start_ms),
        }
        (positive_events if category == "positive" else negative_segments).append(record)

    cap.release()
    cv2.destroyAllWindows()

    output = {
        "dataset_version": "pilot-v1",
        "annotation_round": 1,
        "annotator": "Nguyen Duc Huy",
        "storage_location": "Google Drive (Restricted - Group 3 Internal)",
        "clips": [
            {
                "clip_id": video_path.stem,
                "participant_id": "P01",
                "duration_ms": last_ms,
                "ground_truth_events": positive_events,
                "negative_control_segments": negative_segments,
            }
        ],
    }

    out_path = Path("docs/evaluation/pilot-labels.v1.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
        f.write("\n")

    print(f"\nDa xuat file nhan thanh cong tai: {out_path}")


if __name__ == "__main__":
    main()