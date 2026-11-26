from dataclasses import dataclass, field


@dataclass
class TemporalRuleConfig:
    event_type: str
    onset_sec: float      # Thời gian duy trì tối thiểu để xác nhận sự kiện
    offset_sec: float     # Thời gian ổn định trở lại để đóng sự kiện
    cooldown_sec: float   # Thời gian nghỉ sau khi đóng sự kiện


@dataclass
class EngineConfig:
    engine_version: str = "1.0.0"

    # Hệ số làm mượt EMA (0 < alpha <= 1)
    ema_alpha: float = 0.4
    # Thời gian chịu đựng khi mất landmarks thoáng qua (giây)
    landmark_grace_sec: float = 0.5

    # Ngưỡng vật lý (Hysteresis: ngưỡng vào != ngưỡng thoát để chống nhấp nháy)
    ear_onset_threshold: float = 0.20
    ear_offset_threshold: float = 0.25

    mar_onset_threshold: float = 0.60
    mar_offset_threshold: float = 0.40

    yaw_onset_deg: float = 30.0
    yaw_offset_deg: float = 15.0
    pitch_onset_deg: float = 25.0
    pitch_offset_deg: float = 15.0

    # 5 quy tắc khớp đúng enum trong shared/schemas/event.schema.json
    eyes_closed: TemporalRuleConfig = field(
        default_factory=lambda: TemporalRuleConfig(
            event_type="EYES_CLOSED",
            onset_sec=3.0,
            offset_sec=2.0,
            cooldown_sec=5.0,
        )
    )
    mouth_open: TemporalRuleConfig = field(
        default_factory=lambda: TemporalRuleConfig(
            event_type="MOUTH_OPEN",
            onset_sec=2.0,
            offset_sec=1.5,
            cooldown_sec=8.0,
        )
    )
    head_turned: TemporalRuleConfig = field(
        default_factory=lambda: TemporalRuleConfig(
            event_type="HEAD_TURNED",
            onset_sec=5.0,
            offset_sec=2.0,
            cooldown_sec=5.0,
        )
    )
    face_not_detected: TemporalRuleConfig = field(
        default_factory=lambda: TemporalRuleConfig(
            event_type="FACE_NOT_DETECTED",
            onset_sec=2.5,
            offset_sec=2.0,
            cooldown_sec=5.0,
        )
    )
    multiple_faces: TemporalRuleConfig = field(
        default_factory=lambda: TemporalRuleConfig(
            event_type="MULTIPLE_FACES",
            onset_sec=2.5,
            offset_sec=2.0,
            cooldown_sec=5.0,
        )
    )