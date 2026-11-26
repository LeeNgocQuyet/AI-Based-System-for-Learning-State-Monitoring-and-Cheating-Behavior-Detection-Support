from __future__ import annotations

import sys
from pathlib import Path

_ENGINE_DIR = str(Path(__file__).resolve().parent)
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

import json
import unittest
from datetime import datetime, timedelta, timezone

from reason_logger import AlertReasonLogger
from run_engine import load_signal_stream
from state_machine import RulesEngineV1

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_SCHEMA_PATH = REPO_ROOT / "shared" / "schemas" / "raw-signals.schema.json"
EVENT_SCHEMA_PATH = REPO_ROOT / "shared" / "schemas" / "event.schema.json"
SAMPLE_SIGNAL_PATH = REPO_ROOT / "shared" / "examples" / "raw-signals.sample.json"
UNAVAILABLE_SIGNAL_PATH = REPO_ROOT / "shared" / "examples" / "raw-signals.unavailable.json"


def make_raw_signal(
    seq: int,
    offset_ms: int,
    quality: str = "ok",
    face_count: int | None = 1,
    ear: float | None = 0.30,
    mar: float | None = 0.15,
    yaw: float | None = 0.0,
    pitch: float | None = 0.0,
    roll: float | None = 0.0,
    source: str = "webcam",
) -> dict:
    base_time = datetime(2026, 11, 20, 9, 0, 0, tzinfo=timezone.utc)
    ts = (base_time + timedelta(milliseconds=offset_ms)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    if quality == "unavailable":
        measurements = {
            "face_count": None,
            "eye_aspect_ratio_left": None,
            "eye_aspect_ratio_right": None,
            "mouth_aspect_ratio": None,
            "head_pose_deg": None,
        }
    else:
        head_pose = (
            {"yaw": yaw, "pitch": pitch, "roll": roll}
            if (yaw is not None and pitch is not None and roll is not None)
            else None
        )
        measurements = {
            "face_count": face_count,
            "eye_aspect_ratio_left": ear,
            "eye_aspect_ratio_right": ear,
            "mouth_aspect_ratio": mar,
            "head_pose_deg": head_pose,
        }

    return {
        "schema_version": "0.1.0-draft",
        "schema_status": "DRAFT",
        "is_synthetic": True,
        "session_id": "sess-t16-eval",
        "source_id": "cam-01",
        "timestamp": ts,
        "source": source,
        "sequence": seq,
        "offset_ms": offset_ms,
        "quality": quality,
        "measurements": measurements,
    }


class TestRulesEngineV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if HAS_JSONSCHEMA:
            cls.raw_schema = json.loads(RAW_SCHEMA_PATH.read_text(encoding="utf-8"))
            cls.event_schema = json.loads(EVENT_SCHEMA_PATH.read_text(encoding="utf-8"))

    def assertValidEventAndReasonLog(self, event: dict, logger: AlertReasonLogger):
        if HAS_JSONSCHEMA:
            jsonschema.validate(instance=event, schema=self.event_schema)
        self.assertIsNone(event["severity"])
        self.assertEqual(set(event["evidence"].keys()), {"first_sequence", "last_sequence"})
        self.assertGreaterEqual(event["duration_ms"], 0)

        # Kiểm tra có log lý do cảnh báo tương ứng với event_id và dùng ngôn ngữ trung tính
        matching_logs = [e for e in logger.get_emitted_logs() if e.event_id == event["event_id"]]
        self.assertEqual(len(matching_logs), 1)
        log_entry = matching_logs[0]
        self.assertTrue(len(log_entry.reason) > 10)
        self.assertNotIn("gian lận", log_entry.reason.lower())
        self.assertNotIn("cheating", log_entry.reason.lower())

    def run_stream(self, stream: list[dict]) -> tuple[list[dict], AlertReasonLogger]:
        logger = AlertReasonLogger(enable_stdlib_log=False)
        engine = RulesEngineV1(reason_logger=logger, validate_schemas=True)
        events = engine.process_stream(stream, flush_at_end=True)
        for ev in events:
            self.assertValidEventAndReasonLog(ev, logger)
        return events, logger

    # --- 1. Tích hợp trực tiếp các fixture mẫu có sẵn của repo ---

    def test_integration_with_repo_sample_fixtures(self):
        """Đảm bảo engine đọc và xử lý được raw-signals.sample.json & unavailable.json."""
        sample_frames = load_signal_stream(SAMPLE_SIGNAL_PATH)
        unavailable_frames = load_signal_stream(UNAVAILABLE_SIGNAL_PATH)
        events, _ = self.run_stream(sample_frames + unavailable_frames)
        self.assertIsInstance(events, list)

    # --- 2. Kiểm thử dương tính cả 5 hành vi & reason logging ---

    def test_all_five_positive_rules_and_reason_logs(self):
        """Phát hiện đúng cả 5 sự kiện theo schema và ghi đủ 5 log lý do cảnh báo."""
        stream = []
        for seq in range(320):  # 32 giây (10 FPS)
            ms = seq * 100
            face_count = 1
            ear, mar, yaw = 0.32, 0.15, 0.0

            if 1000 <= ms <= 4500:
                ear = 0.10        # EYES_CLOSED (3.5s)
            elif 7000 <= ms <= 9500:
                mar = 0.78        # MOUTH_OPEN (2.5s)
            elif 12000 <= ms <= 17500:
                yaw = 42.0        # HEAD_TURNED (5.5s)
            elif 20000 <= ms <= 23000:
                face_count = 0    # FACE_NOT_DETECTED (3.0s)
            elif 26000 <= ms <= 29000:
                face_count = 2    # MULTIPLE_FACES (3.0s)

            stream.append(
                make_raw_signal(seq, ms, source="video", face_count=face_count, ear=ear, mar=mar, yaw=yaw)
            )

        events, logger = self.run_stream(stream)
        detected = {e["event_type"] for e in events}
        self.assertEqual(
            detected,
            {"EYES_CLOSED", "MOUTH_OPEN", "HEAD_TURNED", "FACE_NOT_DETECTED", "MULTIPLE_FACES"},
        )
        self.assertEqual(len(logger.get_emitted_logs()), 5)

    # --- 3. Bộ kiểm thử False Positive Cases (Ca âm tính dễ gây báo nhầm) ---

    def test_fp_natural_blink_suppressed(self):
        """FP Case 1: Chớp mắt tự nhiên 400ms không sinh EYES_CLOSED và ghi log từ chối."""
        stream = [
            make_raw_signal(seq, seq * 100, ear=(0.12 if 500 <= seq * 100 <= 900 else 0.32))
            for seq in range(30)
        ]
        events, logger = self.run_stream(stream)
        self.assertEqual(len(events), 0)
        suppressed = [e for e in logger.get_suppressed_logs() if e.event_type == "EYES_CLOSED"]
        self.assertGreaterEqual(len(suppressed), 1)
        self.assertEqual(suppressed[0].decision, "SUPPRESSED_SHORT_DURATION")

    def test_fp_talking_intermittent_mouth_open_suppressed(self):
        """FP Case 2: Nói chuyện / đọc nhẩm (mở miệng ngắt quãng 0.7s mỗi nhịp) không báo MOUTH_OPEN."""
        stream = []
        for seq in range(120):  # 12 giây
            ms = seq * 100
            # Chu kỳ nói 1.3s: 0.7s mở miệng (MAR=0.68), 0.6s khép miệng (MAR=0.22)
            cycle_ms = ms % 1300
            mar = 0.68 if cycle_ms < 700 else 0.22
            stream.append(make_raw_signal(seq, ms, mar=mar))

        events, logger = self.run_stream(stream)
        self.assertEqual(len(events), 0)
        suppressed = [e for e in logger.get_suppressed_logs() if e.event_type == "MOUTH_OPEN"]
        self.assertGreaterEqual(len(suppressed), 1)

    def test_fp_looking_down_writing_notes_suppressed(self):
        """FP Case 3: Cúi đầu viết nháp (pitch ~20°, EAR ~0.22 + liếc nhanh 2s) không báo nhầm."""
        stream = []
        for seq in range(100):  # 10 giây
            ms = seq * 100
            # Cúi nháp bài: pitch = 20° (< 25°), EAR = 0.22 (> 0.20), có lúc cúi sâu 28° trong 1.8s (< 5.0s)
            pitch = 28.0 if 3000 <= ms <= 4800 else 20.0
            stream.append(make_raw_signal(seq, ms, ear=0.22, pitch=pitch, yaw=4.0))

        events, _ = self.run_stream(stream)
        self.assertEqual(len(events), 0)

    def test_fp_passerby_brief_multiple_faces_suppressed(self):
        """FP Case 4: Người đi ngang qua phía sau trong 1.2s (< 2.5s) không báo MULTIPLE_FACES."""
        stream = [
            make_raw_signal(seq, seq * 100, face_count=(2 if 1000 <= seq * 100 <= 2200 else 1))
            for seq in range(45)
        ]
        events, logger = self.run_stream(stream)
        self.assertEqual(len(events), 0)
        suppressed = [e for e in logger.get_suppressed_logs() if e.event_type == "MULTIPLE_FACES"]
        self.assertEqual(len(suppressed), 1)

    def test_fp_low_light_degraded_and_brief_dropout(self):
        """FP Case 5: Ánh sáng yếu (quality=degraded) và mất mặt 1.0s không gây báo giả."""
        stream = []
        for seq in range(60):
            ms = seq * 100
            if 1500 <= ms <= 2500:
                # Mất nhận diện mặt 1.0s (< 2.5s onset)
                stream.append(make_raw_signal(seq, ms, quality="degraded", face_count=0))
            else:
                stream.append(make_raw_signal(seq, ms, quality="degraded", face_count=1, ear=0.23, mar=0.20))

        events, _ = self.run_stream(stream)
        self.assertEqual(len(events), 0)

    def test_fp_cooldown_prevents_duplicate_alert_spam(self):
        """FP Case 6: Trong thời gian cooldown 5s sau khi đóng sự kiện, không bắn trùng lặp cảnh báo."""
        stream = []
        for seq in range(120):  # 12 giây
            ms = seq * 100
            # Đợt 1: nhắm mắt 1.0s -> 4.2s (3.2s >= 3.0s) -> mở mắt 4.3s -> 6.5s -> OFFSET tại 6.5s
            # Đợt 2: nhắm mắt lại ngay ở 7.0s -> 10.2s (nằm trong cooldown 5s sau 6.5s)
            if (1000 <= ms <= 4200) or (7000 <= ms <= 10200):
                ear = 0.10
            else:
                ear = 0.32
            stream.append(make_raw_signal(seq, ms, ear=ear))

        events, logger = self.run_stream(stream)
        self.assertEqual(len(events), 1)
        cooldown_logs = [e for e in logger.get_suppressed_logs() if e.decision == "SUPPRESSED_COOLDOWN"]
        self.assertGreaterEqual(len(cooldown_logs), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)