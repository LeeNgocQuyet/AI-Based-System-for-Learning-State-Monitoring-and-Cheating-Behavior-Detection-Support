"""Validate scaffolding and synthetic contracts, never application behavior."""

from copy import deepcopy
from datetime import datetime
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError
import yaml

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_payload(payload, validator):
    validator.validate(payload)
    if "event_type" not in payload:
        return
    start = datetime.fromisoformat(payload["started_at"].replace("Z", "+00:00"))
    end = datetime.fromisoformat(payload["ended_at"].replace("Z", "+00:00"))
    emitted = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
    require(end >= start, "Event ends before it starts")
    require(emitted >= end, "Closed interval emitted before end")
    elapsed = (end - start).total_seconds() * 1000
    require(abs(elapsed - payload["duration_ms"]) < 0.001, "UTC interval/duration mismatch")
    require(payload["end_offset_ms"] - payload["start_offset_ms"] == payload["duration_ms"],
            "Relative interval/duration mismatch")
    evidence = payload["evidence"]
    if evidence is not None:
        require(evidence["first_sequence"] <= evidence["last_sequence"], "Reversed evidence range")


def main():
    manifest = json.loads((ROOT / "scripts/foundation-files.json").read_text(encoding="utf-8"))
    require(len(manifest) == len(set(manifest)), "Duplicate manifest paths")
    for name in manifest:
        path = ROOT / name
        require(path.is_file(), f"Missing foundation file: {name}")
        content = path.read_bytes()
        content.decode("utf-8")
        require(content.endswith(b"\n"), f"Missing final newline: {name}")
        require(b"\r" not in content, f"Expected LF line endings: {name}")

    # BaseLoader preserves YAML 'on' rather than interpreting it as YAML 1.1 boolean.
    workflow = yaml.load((ROOT / ".github/workflows/ci.yml").read_text(), Loader=yaml.BaseLoader)
    require("pull_request" in workflow["on"], "CI must run on pull requests")
    require(workflow["permissions"]["contents"] == "read", "CI needs read-only contents")
    require(workflow["jobs"]["foundation"]["name"] == "Repository foundation", "Check name changed")
    for path in (ROOT / ".github/ISSUE_TEMPLATE").glob("*.md"):
        frontmatter = path.read_text(encoding="utf-8").split("---", 2)
        require(len(frontmatter) == 3, f"Missing issue frontmatter: {path.name}")
        metadata = yaml.safe_load(frontmatter[1])
        require(all(key in metadata for key in ("name", "about", "title")), "Incomplete template")

    validators = {}
    for kind in ("raw-signals", "event"):
        schema = json.loads((ROOT / f"shared/schemas/{kind}.schema.json").read_text())
        Draft202012Validator.check_schema(schema)
        require("DRAFT" in schema["title"], "Schema must stay visibly DRAFT")
        validators[kind] = Draft202012Validator(schema, format_checker=FormatChecker())

    fixtures = {}
    for path in sorted((ROOT / "shared/examples").glob("*.json")):
        kind = path.name.split(".")[0]
        require(kind in validators, f"Unmapped fixture: {path.name}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        require(payload.get("is_synthetic") is True, "Fixtures must be marked synthetic")
        for key in ("session_id", "source_id", "event_id"):
            if key in payload:
                require(payload[key].startswith("synthetic-"), f"Non-synthetic identifier: {key}")
        validate_payload(payload, validators[kind])
        fixtures[path.name] = payload

    # Contract rejection checks: these do not claim any module has been implemented.
    cases = []
    for field, value in (("timestamp", "not-a-dateZ"), ("duration_ms", -1),
                         ("duration_ms", 1), ("event_type", "CHEATING"),
                         ("source", "browser"), ("unexpected", True)):
        bad = deepcopy(fixtures["event.sample.json"])
        bad[field] = value
        cases.append(("event", bad))
    bad = deepcopy(fixtures["raw-signals.unavailable.json"])
    bad["measurements"]["face_count"] = 0
    cases.append(("raw-signals", bad))
    for kind, bad in cases:
        try:
            validate_payload(bad, validators[kind])
        except (ValueError, ValidationError):
            continue
        raise ValueError("Invalid contract example was unexpectedly accepted")

    print(f"PASS: {len(manifest)} foundation files, 2 DRAFT schemas, "
          f"{len(fixtures)} synthetic fixtures, {len(cases)} rejection checks.")
    print("No application tests, AI benchmarks or user study were performed.")


if __name__ == "__main__":
    main()
