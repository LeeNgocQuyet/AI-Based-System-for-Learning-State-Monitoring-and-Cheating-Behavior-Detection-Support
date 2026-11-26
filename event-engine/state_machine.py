from __future__ import annotations

import sys
from pathlib import Path

_ENGINE_DIR = str(Path(__file__).resolve().parent)
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

import json
import math
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Optional

from reason_logger import AlertReasonLogger
from rules_config import EngineConfig, TemporalRuleConfig

try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_RAW_SCHEMA_PATH = REPO_ROOT / "shared" / "schemas" / "raw-signals.schema.json"
DEFAULT_EVENT_SCHEMA_PATH = REPO_ROOT / "shared" / "schemas" / "event.schema.json"


class RuleState(str, Enum):
    IDLE = "IDLE"
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COOLDOWN = "COOLDOWN"


@dataclass
class FrameContext:
    session_id: str
    source_id: str
    source: str
    is_synthetic: bool
    timestamp: str
    sequence: int
    offset_ms: int
    quality: str


class EMASmoother:
    """Bộ lọc làm mượt tín hiệu liên tục và bỏ qua giá trị None/NaN."""

    def __init__(self, alpha: float):
        self.alpha = alpha
        self.value: Optional[float] = None

    def update(self, raw_val: Optional[float]) -> Optional[float]:
        if raw_val is None or (isinstance(raw_val, float) and math.isnan(raw_val)):
            return self.value
        if self.value is None:
            self.value = float(raw_val)
        else:
            self.value = self.alpha * float(raw_val) + (1.0 - self.alpha) * self.value
        return self.value

    def reset(self) -> None:
        self.value = None


class TemporalRuleTracker:
    """Theo dõi trạng thái hành vi theo thời gian, xuất JSON chuẩn schema và ghi log lý do."""

    def __init__(
        self,
        cfg: TemporalRuleConfig,
        reason_logger: AlertReasonLogger,
        grace_sec: float = 0.5,
    ):
        self.cfg = cfg
        self.reason_logger = reason_logger
        self.grace_sec = grace_sec
        self.state = RuleState.IDLE

        self.condition_timer: float = 0.0
        self.recovery_timer: float = 0.0
        self.cooldown_timer: float = 0.0
        self.missing_timer: float = 0.0
        self._cooldown_logged: bool = False

        self.started_at: Optional[str] = None
        self.start_offset_ms: Optional[int] = None
        self.first_sequence: Optional[int] = None

        self.last_violating_at: Optional[str] = None
        self.last_violating_offset_ms: Optional[int] = None
        self.last_violating_sequence: Optional[int] = None
        self.last_metrics: Dict[str, Any] = {}
        self.last_observation_desc: str = ""

    def reset(self) -> None:
        self.state = RuleState.IDLE
        self.condition_timer = 0.0
        self.recovery_timer = 0.0
        self.cooldown_timer = 0.0
        self.missing_timer = 0.0
        self._cooldown_logged = False
        self.started_at = None
        self.start_offset_ms = None
        self.first_sequence = None
        self.last_violating_at = None
        self.last_violating_offset_ms = None
        self.last_violating_sequence = None
        self.last_metrics = {}
        self.last_observation_desc = ""

    def _record_violation_point(
        self,
        ctx: FrameContext,
        metrics: Dict[str, Any],
        observation_desc: str,
    ) -> None:
        if self.started_at is None:
            self.started_at = ctx.timestamp
            self.start_offset_ms = ctx.offset_ms
            self.first_sequence = ctx.sequence
        self.last_violating_at = ctx.timestamp
        self.last_violating_offset_ms = ctx.offset_ms
        self.last_violating_sequence = ctx.sequence
        self.last_metrics = {**metrics, "quality": ctx.quality}
        self.last_observation_desc = observation_desc

    def _build_event_and_log(self, ctx: FrameContext, close_reason_suffix: str) -> Dict[str, Any]:
        assert self.started_at is not None
        assert self.start_offset_ms is not None
        assert self.first_sequence is not None

        ended_at = self.last_violating_at or ctx.timestamp
        end_offset_ms = (
            self.last_violating_offset_ms
            if self.last_violating_offset_ms is not None
            else ctx.offset_ms
        )
        end_offset_ms = max(self.start_offset_ms, end_offset_ms)
        last_seq = (
            self.last_violating_sequence
            if self.last_violating_sequence is not None
            else ctx.sequence
        )
        last_seq = max(self.first_sequence, last_seq)
        duration_ms = end_offset_ms - self.start_offset_ms
        event_id = f"evt-{uuid.uuid4().hex[:12]}"

        event_payload: Dict[str, Any] = {
            "schema_version": "0.1.0-draft",
            "schema_status": "DRAFT",
            "is_synthetic": ctx.is_synthetic,
            "session_id": ctx.session_id,
            "source_id": ctx.source_id,
            "timestamp": ctx.timestamp,
            "source": ctx.source,
            "event_id": event_id,
            "event_type": self.cfg.event_type,
            "started_at": self.started_at,
            "ended_at": ended_at,
            "start_offset_ms": self.start_offset_ms,
            "end_offset_ms": end_offset_ms,
            "duration_ms": duration_ms,
            "severity": None,
            "evidence": {
                "first_sequence": self.first_sequence,
                "last_sequence": last_seq,
            },
        }

        reason_text = (
            f"{self.last_observation_desc}; duy trì {duration_ms}ms "
            f"(>= ngưỡng kích hoạt {int(self.cfg.onset_sec * 1000)}ms), {close_reason_suffix}"
        )
        self.reason_logger.log(
            timestamp=ctx.timestamp,
            session_id=ctx.session_id,
            source_id=ctx.source_id,
            event_type=self.cfg.event_type,
            decision="EMITTED",
            reason=reason_text,
            event_id=event_id,
            first_sequence=self.first_sequence,
            last_sequence=last_seq,
            duration_ms=duration_ms,
            metrics=self.last_metrics,
        )
        return event_payload

    def step(
        self,
        dt: float,
        ctx: FrameContext,
        is_violating: Optional[bool],
        is_recovered: Optional[bool],
        metrics: Optional[Dict[str, Any]] = None,
        observation_desc: str = "",
    ) -> Optional[Dict[str, Any]]:
        metrics = metrics or {}

        # 1. Xử lý mất tín hiệu / mất landmarks (is_violating is None)
        if is_violating is None:
            self.missing_timer += dt
            if self.missing_timer > self.grace_sec:
                if self.state == RuleState.ACTIVE:
                    event = self._build_event_and_log(
                        ctx,
                        f"đóng sự kiện do mất tín hiệu vượt quá {int(self.grace_sec * 1000)}ms",
                    )
                    self.reset()
                    return event
                if self.state == RuleState.PENDING:
                    candidate_ms = int(round(self.condition_timer * 1000))
                    self.reason_logger.log(
                        timestamp=ctx.timestamp,
                        session_id=ctx.session_id,
                        source_id=ctx.source_id,
                        event_type=self.cfg.event_type,
                        decision="RESET_SIGNAL_LOST",
                        reason=(
                            f"Hủy ứng viên {self.cfg.event_type} sau {candidate_ms}ms "
                            f"do mất landmarks/tín hiệu quá {int(self.grace_sec * 1000)}ms"
                        ),
                        first_sequence=self.first_sequence,
                        last_sequence=ctx.sequence,
                        duration_ms=candidate_ms,
                        metrics={**self.last_metrics, "quality": ctx.quality},
                    )
                self.reset()
            return None

        self.missing_timer = 0.0

        # 2. Trạng thái COOLDOWN
        if self.state == RuleState.COOLDOWN:
            if is_violating and not self._cooldown_logged:
                self._cooldown_logged = True
                self.reason_logger.log(
                    timestamp=ctx.timestamp,
                    session_id=ctx.session_id,
                    source_id=ctx.source_id,
                    event_type=self.cfg.event_type,
                    decision="SUPPRESSED_COOLDOWN",
                    reason=(
                        f"Bỏ qua lặp cảnh báo {self.cfg.event_type} trong thời gian nghỉ "
                        f"({int(self.cfg.cooldown_sec * 1000)}ms)"
                    ),
                    first_sequence=ctx.sequence,
                    last_sequence=ctx.sequence,
                    metrics={**metrics, "quality": ctx.quality},
                )
            self.cooldown_timer += dt
            if self.cooldown_timer >= self.cfg.cooldown_sec:
                self.reset()
            return None

        # 3. Trạng thái IDLE
        if self.state == RuleState.IDLE:
            if is_violating:
                self.state = RuleState.PENDING
                self.condition_timer = dt
                self._record_violation_point(ctx, metrics, observation_desc)
                if self.condition_timer >= self.cfg.onset_sec:
                    self.state = RuleState.ACTIVE
            return None

        # 4. Trạng thái PENDING (Chống nhiễu trước khi đủ onset_sec)
        if self.state == RuleState.PENDING:
            if is_violating:
                self.condition_timer += dt
                self._record_violation_point(ctx, metrics, observation_desc)
                if self.condition_timer >= self.cfg.onset_sec:
                    self.state = RuleState.ACTIVE
            else:
                candidate_ms = int(round(self.condition_timer * 1000))
                self.reason_logger.log(
                    timestamp=ctx.timestamp,
                    session_id=ctx.session_id,
                    source_id=ctx.source_id,
                    event_type=self.cfg.event_type,
                    decision="SUPPRESSED_SHORT_DURATION",
                    reason=(
                        f"Loại bỏ nhiễu {self.cfg.event_type}: chỉ kéo dài {candidate_ms}ms "
                        f"(< ngưỡng kích hoạt {int(self.cfg.onset_sec * 1000)}ms) trước khi tín hiệu ổn định lại"
                    ),
                    first_sequence=self.first_sequence,
                    last_sequence=ctx.sequence,
                    duration_ms=candidate_ms,
                    metrics={**metrics, "quality": ctx.quality},
                )
                self.reset()
            return None

        # 5. Trạng thái ACTIVE (Đang ghi nhận hành vi)
        if self.state == RuleState.ACTIVE:
            if is_violating:
                self._record_violation_point(ctx, metrics, observation_desc)
                self.recovery_timer = 0.0
            elif is_recovered:
                self.recovery_timer += dt
                if self.recovery_timer >= self.cfg.offset_sec:
                    event = self._build_event_and_log(
                        ctx,
                        f"tín hiệu trở lại vùng bình thường trong {int(self.cfg.offset_sec * 1000)}ms",
                    )
                    self.state = RuleState.COOLDOWN
                    self.cooldown_timer = 0.0
                    self.recovery_timer = 0.0
                    self._cooldown_logged = False
                    self.started_at = None
                    self.start_offset_ms = None
                    self.first_sequence = None
                    self.last_violating_at = None
                    self.last_violating_offset_ms = None
                    self.last_violating_sequence = None
                    return event
            else:
                # Vùng trễ (hysteresis band): giữ nguyên trạng thái ACTIVE, chưa reset recovery
                self.recovery_timer = 0.0
            return None

        return None

    def flush(self, ctx: FrameContext) -> Optional[Dict[str, Any]]:
        """Chốt và xuất sự kiện nếu phiên học/video kết thúc khi rule vẫn đang ACTIVE."""
        if self.state == RuleState.ACTIVE:
            event = self._build_event_and_log(ctx, "đóng sự kiện khi kết thúc luồng tín hiệu")
            self.reset()
            return event
        self.reset()
        return None


class RulesEngineV1:
    """
    Rules Engine v1 (Task T16):
    - Nhận luồng raw signals từ ai-core (khớp raw-signals.schema.json)
    - Làm mượt tín hiệu, chống nhiễu dương tính giả, xử lý mất landmarks & cooldown
    - Xuất danh sách event JSON chuẩn event.schema.json kèm logging lý do cảnh báo
    """

    def __init__(
        self,
        config: Optional[EngineConfig] = None,
        reason_logger: Optional[AlertReasonLogger] = None,
        validate_schemas: bool = True,
    ):
        self.cfg = config or EngineConfig()
        self.reason_logger = reason_logger or AlertReasonLogger()
        self.validate_schemas = validate_schemas and HAS_JSONSCHEMA

        self.raw_schema: Optional[Dict[str, Any]] = None
        self.event_schema: Optional[Dict[str, Any]] = None
        if self.validate_schemas:
            if DEFAULT_RAW_SCHEMA_PATH.exists():
                self.raw_schema = json.loads(DEFAULT_RAW_SCHEMA_PATH.read_text(encoding="utf-8"))
            if DEFAULT_EVENT_SCHEMA_PATH.exists():
                self.event_schema = json.loads(DEFAULT_EVENT_SCHEMA_PATH.read_text(encoding="utf-8"))

        self.last_offset_ms: Optional[int] = None
        self.last_ctx: Optional[FrameContext] = None

        self.ear_smoother = EMASmoother(self.cfg.ema_alpha)
        self.mar_smoother = EMASmoother(self.cfg.ema_alpha)
        self.yaw_smoother = EMASmoother(self.cfg.ema_alpha)
        self.pitch_smoother = EMASmoother(self.cfg.ema_alpha)

        self.trackers: Dict[str, TemporalRuleTracker] = {
            "eyes_closed": TemporalRuleTracker(
                self.cfg.eyes_closed, self.reason_logger, self.cfg.landmark_grace_sec
            ),
            "mouth_open": TemporalRuleTracker(
                self.cfg.mouth_open, self.reason_logger, self.cfg.landmark_grace_sec
            ),
            "head_turned": TemporalRuleTracker(
                self.cfg.head_turned, self.reason_logger, self.cfg.landmark_grace_sec
            ),
            "face_not_detected": TemporalRuleTracker(
                self.cfg.face_not_detected, self.reason_logger, self.cfg.landmark_grace_sec
            ),
            "multiple_faces": TemporalRuleTracker(
                self.cfg.multiple_faces, self.reason_logger, self.cfg.landmark_grace_sec
            ),
        }

    @staticmethod
    def _compute_avg_ear(left: Optional[float], right: Optional[float]) -> Optional[float]:
        valid = [v for v in (left, right) if v is not None]
        if not valid:
            return None
        return sum(valid) / len(valid)

    def _validate_input(self, payload: Dict[str, Any]) -> None:
        if self.validate_schemas and self.raw_schema is not None:
            jsonschema.validate(instance=payload, schema=self.raw_schema)

    def _validate_outputs(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if self.validate_schemas and self.event_schema is not None:
            for ev in events:
                jsonschema.validate(instance=ev, schema=self.event_schema)
        return events

    def process_raw_signal(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        self._validate_input(payload)

        quality = str(payload.get("quality", "unavailable"))
        ctx = FrameContext(
            session_id=payload["session_id"],
            source_id=payload["source_id"],
            source=payload["source"],
            is_synthetic=bool(payload["is_synthetic"]),
            timestamp=payload["timestamp"],
            sequence=int(payload["sequence"]),
            offset_ms=int(payload["offset_ms"]),
            quality=quality,
        )

        if self.last_offset_ms is None:
            dt = 0.0
        else:
            dt = max(0.0, (ctx.offset_ms - self.last_offset_ms) / 1000.0)

        self.last_offset_ms = ctx.offset_ms
        self.last_ctx = ctx

        measurements = payload.get("measurements") or {}
        face_count = measurements.get("face_count")
        emitted: List[Dict[str, Any]] = []

        # Trường hợp stream unavailable hoặc face_count là null -> xử lý grace period
        if quality == "unavailable" or face_count is None:
            for tracker in self.trackers.values():
                ev = tracker.step(dt, ctx, None, None)
                if ev:
                    emitted.append(ev)
            return self._validate_outputs(emitted)

        # 1. Đánh giá số lượng khuôn mặt
        ev_no_face = self.trackers["face_not_detected"].step(
            dt=dt,
            ctx=ctx,
            is_violating=(face_count == 0),
            is_recovered=(face_count >= 1),
            metrics={"face_count": face_count},
            observation_desc=f"Số khuôn mặt ghi nhận face_count={face_count} (không phát hiện khuôn mặt)",
        )
        if ev_no_face:
            emitted.append(ev_no_face)

        ev_multi = self.trackers["multiple_faces"].step(
            dt=dt,
            ctx=ctx,
            is_violating=(face_count > 1),
            is_recovered=(face_count <= 1),
            metrics={"face_count": face_count},
            observation_desc=f"Số khuôn mặt ghi nhận face_count={face_count} (> 1 khuôn mặt trong khung hình)",
        )
        if ev_multi:
            emitted.append(ev_multi)

        # 2. Các rule cần landmarks chỉ chạy khi có đúng 1 khuôn mặt
        if face_count != 1:
            for key in ("eyes_closed", "mouth_open", "head_turned"):
                ev = self.trackers[key].step(dt, ctx, None, None)
                if ev:
                    emitted.append(ev)
            return self._validate_outputs(emitted)

        # Trích xuất & làm mượt tín hiệu
        raw_ear = self._compute_avg_ear(
            measurements.get("eye_aspect_ratio_left"),
            measurements.get("eye_aspect_ratio_right"),
        )
        raw_mar = measurements.get("mouth_aspect_ratio")
        head_pose = measurements.get("head_pose_deg")

        ear_s = self.ear_smoother.update(raw_ear) if raw_ear is not None else None
        mar_s = self.mar_smoother.update(raw_mar) if raw_mar is not None else None

        if head_pose is not None:
            yaw_s = self.yaw_smoother.update(head_pose.get("yaw"))
            pitch_s = self.pitch_smoother.update(head_pose.get("pitch"))
        else:
            yaw_s = None
            pitch_s = None

        # Rule: EYES_CLOSED
        if ear_s is not None:
            ear_rounded = round(ear_s, 3)
            ev_eye = self.trackers["eyes_closed"].step(
                dt=dt,
                ctx=ctx,
                is_violating=(ear_s < self.cfg.ear_onset_threshold),
                is_recovered=(ear_s > self.cfg.ear_offset_threshold),
                metrics={"ear_smoothed": ear_rounded, "threshold": self.cfg.ear_onset_threshold},
                observation_desc=(
                    f"Chỉ số mở mắt EAR trung bình={ear_rounded} "
                    f"(< ngưỡng {self.cfg.ear_onset_threshold})"
                ),
            )
            if ev_eye:
                emitted.append(ev_eye)
        else:
            ev_eye = self.trackers["eyes_closed"].step(dt, ctx, None, None)
            if ev_eye:
                emitted.append(ev_eye)

        # Rule: MOUTH_OPEN
        if mar_s is not None:
            mar_rounded = round(mar_s, 3)
            ev_mouth = self.trackers["mouth_open"].step(
                dt=dt,
                ctx=ctx,
                is_violating=(mar_s > self.cfg.mar_onset_threshold),
                is_recovered=(mar_s < self.cfg.mar_offset_threshold),
                metrics={"mar_smoothed": mar_rounded, "threshold": self.cfg.mar_onset_threshold},
                observation_desc=(
                    f"Chỉ số mở miệng MAR={mar_rounded} "
                    f"(> ngưỡng {self.cfg.mar_onset_threshold})"
                ),
            )
            if ev_mouth:
                emitted.append(ev_mouth)
        else:
            ev_mouth = self.trackers["mouth_open"].step(dt, ctx, None, None)
            if ev_mouth:
                emitted.append(ev_mouth)

        # Rule: HEAD_TURNED
        if yaw_s is not None and pitch_s is not None:
            yaw_rounded = round(yaw_s, 2)
            pitch_rounded = round(pitch_s, 2)
            is_head_violating = (
                abs(yaw_s) > self.cfg.yaw_onset_deg or abs(pitch_s) > self.cfg.pitch_onset_deg
            )
            is_head_recovered = (
                abs(yaw_s) < self.cfg.yaw_offset_deg and abs(pitch_s) < self.cfg.pitch_offset_deg
            )
            ev_head = self.trackers["head_turned"].step(
                dt=dt,
                ctx=ctx,
                is_violating=is_head_violating,
                is_recovered=is_head_recovered,
                metrics={
                    "yaw_smoothed": yaw_rounded,
                    "pitch_smoothed": pitch_rounded,
                    "yaw_threshold": self.cfg.yaw_onset_deg,
                    "pitch_threshold": self.cfg.pitch_onset_deg,
                },
                observation_desc=(
                    f"Góc đầu lệch trục yaw={yaw_rounded}°, pitch={pitch_rounded}° "
                    f"(vượt ngưỡng yaw ±{self.cfg.yaw_onset_deg}° / pitch ±{self.cfg.pitch_onset_deg}°)"
                ),
            )
            if ev_head:
                emitted.append(ev_head)
        else:
            ev_head = self.trackers["head_turned"].step(dt, ctx, None, None)
            if ev_head:
                emitted.append(ev_head)

        return self._validate_outputs(emitted)

    def flush(self) -> List[Dict[str, Any]]:
        """Đóng các sự kiện còn đang mở khi kết thúc phiên hoặc hết file video."""
        if self.last_ctx is None:
            return []
        emitted: List[Dict[str, Any]] = []
        for tracker in self.trackers.values():
            ev = tracker.flush(self.last_ctx)
            if ev:
                emitted.append(ev)
        return self._validate_outputs(emitted)

    def process_stream(self, payloads: Iterable[Dict[str, Any]], flush_at_end: bool = True) -> List[Dict[str, Any]]:
        """Tích hợp luồng tín hiệu liên tục từ ai-core và trả về toàn bộ sự kiện hợp lệ."""
        all_events: List[Dict[str, Any]] = []
        for payload in payloads:
            all_events.extend(self.process_raw_signal(payload))
        if flush_at_end:
            all_events.extend(self.flush())
        return all_events


# Giữ alias tương thích ngược với code T09
BehaviorStateMachine = RulesEngineV1