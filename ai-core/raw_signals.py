"""AI Core v1 CLI for extracting raw signals from local video or webcam."""

import argparse
from contextlib import ExitStack
import csv
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import signal
from threading import Event
from time import perf_counter
from uuid import uuid4

import cv2
import mediapipe as mp
import numpy as np

from t03_poc import frame_offset_ms, pose_angles


# Anatomical sides of the subject in the unmirrored input.
LEFT_EYE = (362, 385, 387, 263, 373, 380)
RIGHT_EYE = (33, 160, 158, 133, 153, 144)
INNER_LIPS = (78, 82, 13, 312, 308, 317, 14, 87)
BLENDSHAPES = ("eyeBlinkLeft", "eyeBlinkRight", "jawOpen")
EMPTY_MEASUREMENTS = dict.fromkeys((
    "face_count", "eye_aspect_ratio_left", "eye_aspect_ratio_right",
    "mouth_aspect_ratio", "head_pose_deg",
))
MAX_CONSECUTIVE_READ_FAILURES = 10


def aspect_ratio(points, horizontal, vertical):
    width = np.linalg.norm(points[horizontal[0]] - points[horizontal[1]])
    if not math.isfinite(width) or width <= 0:
        return None
    height = sum(np.linalg.norm(points[top] - points[bottom]) for top, bottom in vertical)
    ratio = float(height / (len(vertical) * width))
    return ratio if math.isfinite(ratio) else None


def eye_ratio(points, indices):
    a, b, c, d, e, f = indices
    return aspect_ratio(points, (a, d), ((b, f), (c, e)))


def measure(result, width, height, detections=None):
    count = len(result.face_landmarks) if detections is None else len(detections)
    measurements = {**EMPTY_MEASUREMENTS, "face_count": count}
    if count != 1 or len(result.face_landmarks) != 1:
        return measurements, "degraded", False

    points = np.array([(point.x * width, point.y * height)
                       for point in result.face_landmarks[0]])
    if detections is not None:
        x, y, box_width, box_height = detections[0][:4]
        center_x, center_y = points.mean(axis=0)
        if not (x <= center_x <= x + box_width and y <= center_y <= y + box_height):
            return measurements, "degraded", False
    measurements["eye_aspect_ratio_left"] = eye_ratio(points, LEFT_EYE)
    measurements["eye_aspect_ratio_right"] = eye_ratio(points, RIGHT_EYE)
    a, b, c, d, e, f, g, h = INNER_LIPS
    measurements["mouth_aspect_ratio"] = aspect_ratio(points, (a, e), ((b, h), (c, g), (d, f)))
    if result.facial_transformation_matrixes:
        matrix = result.facial_transformation_matrixes[0]
        if np.isfinite(matrix).all() and np.linalg.matrix_rank(matrix[:3, :3]) == 3:
            pitch, yaw, roll = pose_angles(matrix)
            if all(map(math.isfinite, (yaw, pitch, roll))):
                measurements["head_pose_deg"] = {"yaw": yaw, "pitch": pitch, "roll": roll}
    quality = "ok" if all(value is not None for value in measurements.values()) else "degraded"
    return measurements, quality, True


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version="AI Core 1.0.0")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video", type=Path)
    source.add_argument("--camera", type=int)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True, help="New output directory")
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--max-faces", type=int, default=2)
    parser.add_argument("--yunet-model", type=Path, help="Optional YuNet ONNX for face count")
    parser.add_argument("--blendshapes", action="store_true", help="Write diagnostic CSV")
    parser.add_argument("--synthetic", action="store_true", help="Mark a constructed fixture")
    parser.add_argument("--video-start-utc", help="Original video start as ISO 8601 UTC, ending in Z")
    args = parser.parse_args()
    if args.max_faces < 2:
        parser.error("--max-faces must be at least 2")
    if args.max_frames is not None and args.max_frames <= 0:
        parser.error("--max-frames must be positive")
    if not args.model.is_file() or (args.video is not None and not args.video.is_file()):
        parser.error("Model and video must be existing files")
    if args.yunet_model is not None and not args.yunet_model.is_file():
        parser.error("YuNet model must be an existing ONNX file")
    if args.video_start_utc is not None:
        try:
            if args.video is None or not args.video_start_utc.endswith("Z"):
                raise ValueError
            args.video_start_utc = datetime.fromisoformat(args.video_start_utc)
        except ValueError:
            parser.error("--video-start-utc requires a video and a valid timestamp ending in Z")
    return args


def run(args, stop):
    is_camera = args.camera is not None
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=args.max_faces,
        output_face_blendshapes=args.blendshapes,
        output_facial_transformation_matrixes=True,
    )
    capture = cv2.VideoCapture(args.camera if is_camera else str(args.video))
    try:
        if not capture.isOpened():
            raise ValueError("Could not open input")
        fps = capture.get(cv2.CAP_PROP_FPS)
        fps = fps if math.isfinite(fps) and fps > 0 else None
        detector = None
        if args.yunet_model is not None:
            detector = cv2.FaceDetectorYN.create(
                str(args.yunet_model), "", (320, 320), 0.85, 0.3, 5000
            )
        args.output.mkdir(parents=True, exist_ok=False)
        with (mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker,
              (args.output / "raw-signals.jsonl").open("x", encoding="utf-8") as output):
            extract(args, capture, landmarker, output, fps, is_camera, detector, stop)
    finally:
        capture.release()


def extract(args, capture, landmarker, output, fps, is_camera, detector, stop):
    source = "webcam" if is_camera else "video"
    session_id = uuid4().hex
    origin = perf_counter()
    start_utc = args.video_start_utc or datetime.now(timezone.utc)
    last_ms = -1
    sequence = 0
    failures = 0
    expected_frames = capture.get(cv2.CAP_PROP_FRAME_COUNT) if not is_camera else None
    with ExitStack() as stack:
        diagnostic = None
        if args.blendshapes:
            file = stack.enter_context((args.output / "blendshapes.csv").open(
                "x", newline="", encoding="utf-8"
            ))
            diagnostic = csv.writer(file)
            diagnostic.writerow(("sequence", "offset_ms", *BLENDSHAPES))
        while not stop.is_set() and (args.max_frames is None or sequence < args.max_frames):
            ok, frame = capture.read()
            if stop.is_set():
                break
            if not ok and not is_camera:
                if expected_frames and sequence < expected_frames:
                    raise ValueError(f"Video read ended at frame {sequence}; container reports {expected_frames:g}")
                break
            last_ms, _ = frame_offset_ms(capture, is_camera, fps, origin, sequence, last_ms)
            scores = {}
            if ok:
                failures = 0
                measurements, quality, scores = analyze_frame(frame, last_ms, landmarker, detector)
            else:
                failures += 1
                measurements, quality = EMPTY_MEASUREMENTS, "unavailable"
            timestamp = start_utc + timedelta(milliseconds=last_ms)
            output.write(json.dumps({
                "schema_version": "0.1.0-draft",
                "schema_status": "DRAFT",
                "is_synthetic": args.synthetic,
                "session_id": session_id,
                "source_id": source,
                "source": source,
                "sequence": sequence,
                "offset_ms": last_ms,
                "timestamp": timestamp.isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                "quality": quality,
                "measurements": measurements,
            }, allow_nan=False) + "\n")
            if diagnostic is not None:
                diagnostic.writerow((sequence, last_ms, *(scores.get(name) for name in BLENDSHAPES)))
            sequence += 1
            if failures >= MAX_CONSECUTIVE_READ_FAILURES:
                raise ValueError(f"Webcam failed {failures} consecutive reads")
            if failures:
                stop.wait(0.05)
    if not sequence and not stop.is_set():
        raise ValueError("No decodable frames in the input")
    print(f"Wrote {sequence} raw signal records to {args.output}")


def analyze_frame(frame, offset_ms, landmarker, detector):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = landmarker.detect_for_video(image, offset_ms)
    height, width = frame.shape[:2]
    detections = None
    if detector is not None:
        if detector.getInputSize() != (width, height):
            detector.setInputSize((width, height))
        _, faces = detector.detect(frame)
        detections = faces if faces is not None else ()
    measurements, quality, matched = measure(result, width, height, detections)
    scores = {item.category_name: item.score for item in result.face_blendshapes[0]} \
        if matched and result.face_blendshapes else {}
    return measurements, quality, scores


if __name__ == "__main__":
    args = parse_args()
    stop = Event()
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    try:
        run(args, stop)
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
