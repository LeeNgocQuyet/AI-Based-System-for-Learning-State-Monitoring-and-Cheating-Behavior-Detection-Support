"""Compare raw head pose with reference angles matched by frame sequence."""

import argparse
import csv
import json
import math
from pathlib import Path
from statistics import mean


AXES = ("yaw", "pitch", "roll")


def load_reference(path):
    reference = {}
    with path.open(encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        if not {"sequence", *AXES}.issubset(reader.fieldnames or ()):
            raise ValueError("Reference CSV needs sequence,yaw,pitch,roll")
        for row in reader:
            sequence = int(row["sequence"])
            angles = {axis: float(row[axis]) for axis in AXES}
            if sequence < 0 or sequence in reference or not all(map(math.isfinite, angles.values())):
                raise ValueError(f"Invalid or duplicate reference at sequence {sequence}")
            reference[sequence] = angles
    if not reference:
        raise ValueError("Reference CSV is empty")
    return reference


def evaluate(raw_path, reference):
    seen = set()
    errors = {axis: [] for axis in AXES}
    with raw_path.open(encoding="utf-8") as file:
        for line in file:
            row = json.loads(line)
            sequence = row["sequence"]
            if sequence not in reference:
                continue
            if sequence in seen:
                raise ValueError(f"Duplicate raw record at sequence {sequence}")
            seen.add(sequence)
            pose = row["measurements"]["head_pose_deg"]
            if pose is None:
                continue
            for axis in AXES:
                delta = pose[axis] - reference[sequence][axis]
                errors[axis].append(abs((delta + 180) % 360 - 180))
    measured = len(errors["yaw"])
    return {
        "reference_frames": len(reference),
        "missing_raw_frames": len(reference) - len(seen),
        "missing_pose_frames": len(seen) - measured,
        "measured_frames": measured,
        "coverage": measured / len(reference),
        "mae_deg": {axis: mean(values) if values else None for axis, values in errors.items()},
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raw", type=Path)
    parser.add_argument("reference", type=Path, help="CSV with sequence,yaw,pitch,roll in degrees")
    args = parser.parse_args()
    try:
        print(json.dumps(evaluate(args.raw, load_reference(args.reference)), indent=2, allow_nan=False))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(str(exc)) from exc
