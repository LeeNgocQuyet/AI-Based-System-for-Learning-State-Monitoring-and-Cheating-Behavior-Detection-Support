from __future__ import annotations

import math
import uuid
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from rules_config import EngineConfig, TemporalRuleConfig

import sys
from pathlib import Path

_ENGINE_DIR = str(Path(__file__).resolve().parent)
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)
    
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
    """Theo dõi trạng thái hành vi theo thời gian và xuất JSON chuẩn event.schema.json."""

    def __init__(self, cfg: TemporalRuleConfig, grace_sec: float = 0.5):
        self.cfg = cfg
        self.grace_sec = grace_sec
        self.state = RuleState.IDLE

        self.condition_timer: float = 0.0
        self.recovery_timer: float = 0.0
        self.cooldown_timer: float = 0.0
        self.missing_timer: float = 0.0

        # Lưu thông tin mốc bắt đầu & kết thúc của một đợt hành vi
        self.started_at: Optional[str] = None
        self.start_offset_ms: Optional[int] = None
        self.first_sequence: Optional[int] = None

        self.last_violating_at: Optional[str] = None
        self.last_violating_offset_ms: Optional[int] = None
        self.last_violating_sequence: Optional[int] = None

    def reset(self) -> None:
        self.state = RuleState.IDLE
        self.condition_timer = 0.0
        self.recovery_timer = 0.0
        self.cooldown_timer = 0.0
        self.missing_timer = 0.0
        self.started_at = None
        self.start_offset_ms = None
        self.first_sequence = None
        self.last_violating_at = None
        self.last_violating_offset_ms = None
        self.last_violating_sequence = None

    def _record_violation_point(self, ctx: FrameContext) -> None:
        if self.started_at is None:
            self.started_at = ctx.timestamp
            self.start_offset_ms = ctx.offset_ms
            self.first_sequence = ctx.sequence
        self.last_violating_at = ctx.timestamp
        self.last_violating_offset_ms = ctx.offset_ms
        self.last_violating_sequence = ctx.sequence

    def _build_event(self, ctx: FrameContext, emit_timestamp: Optional[str] = None) -> Dict[str, Any]:
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

        return {
            "schema_version": "0.1.0-draft",
            "schema_status": "DRAFT",
            "is_synthetic": ctx.is_synthetic,
            "session_id": ctx.session_id,
            "source_id": ctx.source_id,
            "timestamp": emit_timestamp or ctx.timestamp,
            "source": ctx.source,
            "event_id": f"evt-{uuid.uuid4().hex[:12]}",
            "event_type": self.cfg.event_type,
            "started_at": self.started_at,
            "ended_at": ended_at,
            "start_offset_ms": self.start_offset_ms,
            "end_offset_ms": end_offset_ms,
            "duration_ms": end_offset_ms - self.start_offset_ms,
            "severity": None,
            "evidence": {
                "first_sequence": self.first_sequence,
                "last_sequence": last_seq,
            },
        }

    def step(
        self,
        dt: float,
        ctx: FrameContext,
        is_violating: Optional[bool],
        is_recovered: Optional[bool],
    ) -> Optional[Dict[str, Any]]:
        # 1. Xử lý mất tín hiệu / mất landmarks (is_violating is None)
        if is_violating is None:
            self.missing_timer += dt
            if self.missing_timer > self.grace_sec:
                if self.state == RuleState.ACTIVE:
                    event = self._build_event(ctx)
                    self.reset()
                    return event
                self.reset()
            return None

        self.missing_timer = 0.0

        # 2. Trạng thái COOLDOWN
        if self.state == RuleState.COOLDOWN:
            self.cooldown_timer += dt
            if self.cooldown_timer >= self.cfg.cooldown_sec:
                self.reset()
            return None

        # 3. Trạng thái IDLE
        if self.state == RuleState.IDLE:
            if is_violating:
                self.state = RuleState.PENDING
                self.condition_timer = dt
                self._record_violation_point(ctx)
                if self.condition_timer >= self.cfg.onset_sec:
                    self.state = RuleState.ACTIVE
            return None

        # 4. Trạng thái PENDING (Chống nhiễu trước khi đủ onset_sec)
        if self.state == RuleState.PENDING:
            if is_violating:
                self.condition_timer += dt
                self._record_violation_point(ctx)
                if self.condition_timer >= self.cfg.onset_sec:
                    self.state = RuleState.ACTIVE
            else:
                # Tín hiệu giảm dưới ngưỡng trước khi đủ thời gian onset -> bỏ qua nhiễu
                self.reset()
            return None

        # 5. Trạng thái ACTIVE (Đang diễn ra hành vi)
        if self.state == RuleState.ACTIVE:
            if is_violating:
                self._record_violation_point(ctx)
                self.recovery_timer = 0.0
            elif is_recovered:
                self.recovery_timer += dt
                if self.recovery_timer >= self.cfg.offset_sec:
                    event = self._build_event(ctx)
                    self.state = RuleState.COOLDOWN
                    self.cooldown_timer = 0.0
                    self.recovery_timer = 0.0
                    self.started_at = None
                    self.start_offset_ms = None
                    self.first_sequence = None
                    self.last_violating_at = None
                    self.last_violating_offset_ms = None
                    self.last_violating_sequence = None
                    return event
            else:
                # Nằm trong vùng trễ (hysteresis band) giữa onset và offset
                self.recovery_timer = 0.0
            return None

        return None

    def flush(self, ctx: FrameContext) -> Optional[Dict[str, Any]]:
        """Đóng và xuất sự kiện nếu phiên học/video kết thúc khi rule vẫn đang ACTIVE."""
        if self.state == RuleState.ACTIVE:
            event = self._build_event(ctx)
            self.reset()
            return event
        self.reset()
        return None


class BehaviorStateMachine:
    """Engine nhận dict đúng chuẩn raw-signals.schema.json và xuất list dict chuẩn event.schema.json."""

    def __init__(self, config: Optional[EngineConfig] = None):
        self.cfg = config or EngineConfig()
        self.last_offset_ms: Optional[int] = None
        self.last_ctx: Optional[FrameContext] = None

        self.ear_smoother = EMASmoother(self.cfg.ema_alpha)
        self.mar_smoother = EMASmoother(self.cfg.ema_alpha)
        self.yaw_smoother = EMASmoother(self.cfg.ema_alpha)
        self.pitch_smoother = EMASmoother(self.cfg.ema_alpha)

        self.trackers: Dict[str, TemporalRuleTracker] = {
            "eyes_closed": TemporalRuleTracker(self.cfg.eyes_closed, self.cfg.landmark_grace_sec),
            "mouth_open": TemporalRuleTracker(self.cfg.mouth_open, self.cfg.landmark_grace_sec),
            "head_turned": TemporalRuleTracker(self.cfg.head_turned, self.cfg.landmark_grace_sec),
            "face_not_detected": TemporalRuleTracker(self.cfg.face_not_detected, self.cfg.landmark_grace_sec),
            "multiple_faces": TemporalRuleTracker(self.cfg.multiple_faces, self.cfg.landmark_grace_sec),
        }

    @staticmethod
    def _compute_avg_ear(left: Optional[float], right: Optional[float]) -> Optional[float]:
        valid = [v for v in (left, right) if v is not None]
        if not valid:
            return None
        return sum(valid) / len(valid)

    def process_raw_signal(self, payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        ctx = FrameContext(
            session_id=payload["session_id"],
            source_id=payload["source_id"],
            source=payload["source"],
            is_synthetic=bool(payload["is_synthetic"]),
            timestamp=payload["timestamp"],
            sequence=int(payload["sequence"]),
            offset_ms=int(payload["offset_ms"]),
        )

        if self.last_offset_ms is None:
            dt = 0.0
        else:
            dt = max(0.0, (ctx.offset_ms - self.last_offset_ms) / 1000.0)

        self.last_offset_ms = ctx.offset_ms
        self.last_ctx = ctx

        quality = payload.get("quality", "unavailable")
        measurements = payload.get("measurements") or {}
        face_count = measurements.get("face_count")

        emitted: List[Dict[str, Any]] = []

        # Trường hợp stream unavailable hoặc face_count là null -> truyền None để xử lý grace period
        if quality == "unavailable" or face_count is None:
            for tracker in self.trackers.values():
                ev = tracker.step(dt, ctx, None, None)
                if ev:
                    emitted.append(ev)
            return emitted

        # 1. Đánh giá số lượng khuôn mặt
        ev_no_face = self.trackers["face_not_detected"].step(
            dt=dt,
            ctx=ctx,
            is_violating=(face_count == 0),
            is_recovered=(face_count >= 1),
        )
        if ev_no_face:
            emitted.append(ev_no_face)

        ev_multi = self.trackers["multiple_faces"].step(
            dt=dt,
            ctx=ctx,
            is_violating=(face_count > 1),
            is_recovered=(face_count <= 1),
        )
        if ev_multi:
            emitted.append(ev_multi)

        # 2. Các rule cần landmarks chỉ chạy khi có đúng 1 khuôn mặt
        if face_count != 1:
            for key in ("eyes_closed", "mouth_open", "head_turned"):
                ev = self.trackers[key].step(dt, ctx, None, None)
                if ev:
                    emitted.append(ev)
            return emitted

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
            ev_eye = self.trackers["eyes_closed"].step(
                dt=dt,
                ctx=ctx,
                is_violating=(ear_s < self.cfg.ear_onset_threshold),
                is_recovered=(ear_s > self.cfg.ear_offset_threshold),
            )
            if ev_eye:
                emitted.append(ev_eye)
        else:
            ev_eye = self.trackers["eyes_closed"].step(dt, ctx, None, None)
            if ev_eye:
                emitted.append(ev_eye)

        # Rule: MOUTH_OPEN
        if mar_s is not None:
            ev_mouth = self.trackers["mouth_open"].step(
                dt=dt,
                ctx=ctx,
                is_violating=(mar_s > self.cfg.mar_onset_threshold),
                is_recovered=(mar_s < self.cfg.mar_offset_threshold),
            )
            if ev_mouth:
                emitted.append(ev_mouth)
        else:
            ev_mouth = self.trackers["mouth_open"].step(dt, ctx, None, None)
            if ev_mouth:
                emitted.append(ev_mouth)

        # Rule: HEAD_TURNED
        if yaw_s is not None and pitch_s is not None:
            is_head_violating = (abs(yaw_s) > self.cfg.yaw_onset_deg) or (abs(pitch_s) > self.cfg.pitch_onset_deg)
            is_head_recovered = (abs(yaw_s) < self.cfg.yaw_offset_deg) and (abs(pitch_s) < self.cfg.pitch_offset_deg)
            ev_head = self.trackers["head_turned"].step(
                dt=dt,
                ctx=ctx,
                is_violating=is_head_violating,
                is_recovered=is_head_recovered,
            )
            if ev_head:
                emitted.append(ev_head)
        else:
            ev_head = self.trackers["head_turned"].step(dt, ctx, None, None)
            if ev_head:
                emitted.append(ev_head)

        return emitted

    def flush(self) -> List[Dict[str, Any]]:
        """Gọi khi kết thúc phiên/video để chốt các sự kiện vẫn đang diễn ra."""
        if self.last_ctx is None:
            return []
        emitted: List[Dict[str, Any]] = []
        for tracker in self.trackers.values():
            ev = tracker.flush(self.last_ctx)
            if ev:
                emitted.append(ev)
        return emitted