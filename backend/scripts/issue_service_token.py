from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.security import create_service_token
from app.models.enums import EventSource


def main() -> None:
    parser = argparse.ArgumentParser(description="Issue a short-lived local demo token for an AI/System producer")
    parser.add_argument("--service", required=True, choices=["ai-learning", "ai-exam", "system"])
    parser.add_argument("--minutes", type=int, default=60)
    args = parser.parse_args()
    sources = {
        "ai-learning": {EventSource.AI_LEARNING},
        "ai-exam": {EventSource.AI_EXAM},
        "system": {EventSource.SYSTEM},
    }
    if not 1 <= args.minutes <= 240:
        raise SystemExit("--minutes must be between 1 and 240")
    print(create_service_token(args.service, sources[args.service], args.minutes))


if __name__ == "__main__":
    main()
