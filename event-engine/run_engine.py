from __future__ import annotations

import sys
from pathlib import Path

_ENGINE_DIR = str(Path(__file__).resolve().parent)
if _ENGINE_DIR not in sys.path:
    sys.path.insert(0, _ENGINE_DIR)

import argparse
import json
import logging
from typing import Any, Dict, List

from state_machine import RulesEngineV1


def load_signal_stream(input_path: Path) -> List[Dict[str, Any]]:
    raw_text = input_path.read_text(encoding="utf-8").strip()
    if not raw_text:
        return []
    # Hỗ trợ cả JSON object đơn, JSON array [...] hoặc JSONL (mỗi dòng 1 JSON)
    if raw_text.startswith("["):
        return json.loads(raw_text)
    if raw_text.startswith("{") and "\n" not in raw_text:
        return [json.loads(raw_text)]
    try:
        obj = json.loads(raw_text)
        return [obj] if isinstance(obj, dict) else obj
    except json.JSONDecodeError:
        return [json.loads(line) for line in raw_text.splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Rules Engine v1 - AI Signal Integration Runner (T16)")
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("shared/examples/raw-signals.sample.json"),
        help="Đường dẫn file raw-signals (.json hoặc .jsonl) từ ai-core",
    )
    parser.add_argument(
        "--events-out",
        type=Path,
        default=None,
        help="Đường dẫn xuất file events JSON (tùy chọn)",
    )
    parser.add_argument(
        "--logs-out",
        type=Path,
        default=None,
        help="Đường dẫn xuất file reason-logs JSONL (tùy chọn)",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")

    signals = load_signal_stream(args.input)
    engine = RulesEngineV1(validate_schemas=True)
    events = engine.process_stream(signals, flush_at_end=True)

    print(f"Processed {len(signals)} raw signal frame(s) -> Emitted {len(events)} schema-valid event(s).")
    print(json.dumps(events, indent=2, ensure_ascii=False))

    if args.events_out is not None:
        args.events_out.parent.mkdir(parents=True, exist_ok=True)
        with open(args.events_out, "w", encoding="utf-8", newline="\n") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
            f.write("\n")

    if args.logs_out is not None:
        engine.reason_logger.export_jsonl(args.logs_out)


if __name__ == "__main__":
    main()