import json
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from state_machine import BehaviorStateMachine
import sys
from pathlib import Path

_ENGINE_DIR = str(Path(__file__).resolve().parent)
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)
    
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


REPO_ROOT = Path(__file__).resolve().parent.parent
RAW_SCHEMA_PATH = REPO_ROOT / "shared" / "schemas" / "raw-signals.schema.json"
EVENT_SCHEMA_PATH = REPO_ROOT / "shared" / "schemas" / "event.schema.json"


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
) -> dict:
    base_time = datetime(2026, 11, 15, 8, 0, 0, tzinfo=timezone.utc)
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
        "session_id": "sess-demo-001",
        "source_id": "cam-01",
        "timestamp": ts,
        "source": "webcam",
        "sequence": seq,
        "offset_ms": offset_ms,
        "quality": quality,
        "measurements": measurements,
    }


class TestSchemaCompliantStateMachine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if HAS_JSONSCHEMA:
            cls.raw_schema = json.loads(RAW_SCHEMA_PATH.read_text(encoding="utf-8"))
            cls.event_schema = json.loads(EVENT_SCHEMA_PATH.read_text(encoding="utf-8"))

    def assertValidEvent(self, event: dict):
        if HAS_JSONSCHEMA:
            jsonschema.validate(instance=event, schema=self.event_schema)
        self.assertIsNone(event["severity"])
        self.assertEqual(set(event["evidence"].keys()), {"first_sequence", "last_sequence"})
        self.assertGreaterEqual(event["duration_ms"], 0)

    def run_stream(self, payloads: list[dict]) -> list[dict]:
        sm = BehaviorStateMachine()
        events = []
        for p in payloads:
            if HAS_JSONSCHEMA:
                jsonschema.validate(instance=p, schema=self.raw_schema)
            events.extend(sm.process_raw_signal(p))
        events.extend(sm.flush())
        for ev in events:
            self.assertValidEvent(ev)
        return events

    def test_natural_blink_ignored(self):
        """Chớp mắt nhanh 400ms không sinh sự kiện."""
        stream = []
        for seq in range(30):
            ms = seq * 100
            ear = 0.12 if 500 <= ms <= 900 else 0.32
            stream.append(make_raw_signal(seq, ms, ear=ear))
        self.assertEqual(len(self.run_stream(stream)), 0)

    def test_eyes_closed_full_cycle(self):
        """Nhắm mắt 3.5s -> mở mắt 2.5s -> xuất 1 event EYES_CLOSED chuẩn schema."""
        stream = []
        for seq in range(90):  # 9 giây
            ms = seq * 100
            ear = 0.11 if 1000 <= ms <= 4500 else 0.32
            stream.append(make_raw_signal(seq, ms, ear=ear))

        events = self.run_stream(stream)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "EYES_CLOSED")
        self.assertGreaterEqual(events[0]["duration_ms"], 3000)

    def test_unavailable_grace_period(self):
        """Mất tín hiệu 0.2s giữa chừng không làm đứt chuỗi theo dõi."""
        stream = []
        for seq in range(80):
            ms = seq * 100
            if ms in (2500, 2600):
                stream.append(make_raw_signal(seq, ms, quality="unavailable"))
            else:
                ear = 0.11 if 1000 <= ms <= 4500 else 0.32
                stream.append(make_raw_signal(seq, ms, ear=ear))

        events = self.run_stream(stream)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "EYES_CLOSED")

    def test_all_five_rules(self):
        """Kiểm thử đủ 5 loại sự kiện theo schema."""
        stream = []
        for seq in range(320):  # 32 giây
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

            stream.append(make_raw_signal(seq, ms, face_count=face_count, ear=ear, mar=mar, yaw=yaw))

        events = self.run_stream(stream)
        detected = {e["event_type"] for e in events}
        self.assertEqual(
            detected,
            {"EYES_CLOSED", "MOUTH_OPEN", "HEAD_TURNED", "FACE_NOT_DETECTED", "MULTIPLE_FACES"},
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)