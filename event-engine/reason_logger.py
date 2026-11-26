from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ReasonLogEntry:
    timestamp: str
    session_id: str
    source_id: str
    event_type: str
    decision: str  # EMITTED | SUPPRESSED_SHORT_DURATION | SUPPRESSED_COOLDOWN | RESET_SIGNAL_LOST
    reason: str
    event_id: Optional[str] = None
    first_sequence: Optional[int] = None
    last_sequence: Optional[int] = None
    duration_ms: int = 0
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AlertReasonLogger:
    """
    Ghi nhận lý do kích hoạt hoặc từ chối cảnh báo bằng ngôn ngữ quan sát trung tính.
    Tách biệt khỏi payload event.schema.json để không vi phạm additionalProperties: false.
    """

    def __init__(self, logger_name: str = "event_engine.reasons", enable_stdlib_log: bool = True):
        self.entries: List[ReasonLogEntry] = []
        self.enable_stdlib_log = enable_stdlib_log
        self._logger = logging.getLogger(logger_name)

    def log(
        self,
        *,
        timestamp: str,
        session_id: str,
        source_id: str,
        event_type: str,
        decision: str,
        reason: str,
        event_id: Optional[str] = None,
        first_sequence: Optional[int] = None,
        last_sequence: Optional[int] = None,
        duration_ms: int = 0,
        metrics: Optional[Dict[str, Any]] = None,
    ) -> ReasonLogEntry:
        entry = ReasonLogEntry(
            timestamp=timestamp,
            session_id=session_id,
            source_id=source_id,
            event_type=event_type,
            decision=decision,
            reason=reason,
            event_id=event_id,
            first_sequence=first_sequence,
            last_sequence=last_sequence,
            duration_ms=duration_ms,
            metrics=metrics or {},
        )
        self.entries.append(entry)

        if self.enable_stdlib_log:
            level = logging.INFO if decision == "EMITTED" else logging.DEBUG
            self._logger.log(
                level,
                "[%s] %s (%s): %s | seq=%s..%s | duration=%dms | metrics=%s",
                decision,
                event_type,
                event_id or "no-event",
                reason,
                first_sequence,
                last_sequence,
                duration_ms,
                entry.metrics,
            )
        return entry

    def get_emitted_logs(self) -> List[ReasonLogEntry]:
        return [e for e in self.entries if e.decision == "EMITTED"]

    def get_suppressed_logs(self) -> List[ReasonLogEntry]:
        return [e for e in self.entries if e.decision != "EMITTED"]

    def export_jsonl(self, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8", newline="\n") as f:
            for entry in self.entries:
                f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")