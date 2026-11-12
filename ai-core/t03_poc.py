"""Run the T03 Face Landmarker proof of concept on a video or webcam."""

import argparse
import csv
import hashlib
import json
import math
import os
import platform
from pathlib import Path
from time import perf_counter

import cv2
import mediapipe as mp
import numpy as np


FEATURES = {
    "eyes": ((33, 160, 158, 133, 153, 144), (362, 385, 387, 263, 373, 380)),
    "mouth": ((61, 40, 37, 0, 267, 270, 291, 321, 314, 17, 84, 91),),
    "face": ((10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
              397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
              172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109),),
}
COLORS = {"eyes": (0, 255, 0), "mouth": (0, 160, 255), "face": (255, 220, 0)}


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--video", type=Path)
    source.add_argument("--camera", type=int, metavar="INDEX")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--save-video", action="store_true")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--max-frames", type=int)
    parser.add_argument("--warmup", type=int, default=10)
    args = parser.parse_args()
    if args.max_frames is not None and args.max_frames <= 0:
        parser.error("--max-frames must be positive")
    if args.warmup < 0:
        parser.error("--warmup cannot be negative")
    if not args.model.is_file():
        parser.error(f"Model file not found: {args.model}")
    if args.video is not None and not args.video.is_file():
        parser.error(f"Video file not found: {args.video}")
    return args


def pose_angles(matrix):
    # Remove scale and shear before decomposing the canonical-to-face rotation.
    rotation = np.asarray(matrix[:3, :3], dtype=np.float64)
    left, _, right = np.linalg.svd(rotation)
    left[:, -1] *= np.linalg.det(left @ right)
    x, y, z = cv2.RQDecomp3x3(left @ right)[0]
    return (x, y, z)


def frame_offset_ms(capture, is_camera, fps, origin, sequence, last_ms):
    if is_camera:
        timestamp = (perf_counter() - origin) * 1000
        clock = "monotonic_capture"
    else:
        timestamp = capture.get(cv2.CAP_PROP_POS_MSEC)
        clock = "video_position"
        if (not math.isfinite(timestamp) or timestamp < 0
                or (sequence and timestamp <= last_ms)):
            if fps is None:
                raise ValueError("Video has no usable timestamps or nominal FPS")
            timestamp = sequence * 1000 / fps
            clock = "frame_index_over_nominal_fps"
    return max(last_ms + 1, round(timestamp)), clock


def draw_overlay(frame, points, angles):
    if points is not None:
        for feature, contours in FEATURES.items():
            for contour in contours:
                pixels = np.rint(points[list(contour)]).astype(np.int32)
                cv2.polylines(frame, [pixels], True, COLORS[feature], 1, cv2.LINE_AA)
                for x, y in pixels:
                    cv2.circle(frame, (x, y), 2, COLORS[feature], -1, cv2.LINE_AA)
    status = "Face not detected"
    if points is not None:
        status = "Face detected"
    if angles:
        status = "Pose X/Y/Z: {:.1f} / {:.1f} / {:.1f} deg".format(*angles)
    cv2.putText(frame, status, (12, 27), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (255, 255, 255), 1, cv2.LINE_AA)


def run(args):
    options = mp.tasks.vision.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(args.model)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_faces=1,
        output_facial_transformation_matrixes=True,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    source = str(args.video) if args.video is not None else args.camera
    capture = cv2.VideoCapture(source)
    writer = None
    rows = []
    width = height = 0
    last_ms = -1
    previous_points = None
    clock_sources = set()
    try:
        if not capture.isOpened():
            raise ValueError(f"Could not open input: {source}")
        fps = capture.get(cv2.CAP_PROP_FPS)
        fps = fps if math.isfinite(fps) and fps > 0 else None
        backend = capture.getBackendName()
        if args.save_video and fps is None:
            raise ValueError("Input FPS is required to write the overlay video")

        with mp.tasks.vision.FaceLandmarker.create_from_options(options) as landmarker:
            origin = perf_counter()
            while args.max_frames is None or len(rows) < args.max_frames:
                frame_start = perf_counter()
                ok, frame = capture.read()
                if not ok:
                    if args.camera is not None:
                        raise ValueError("Webcam frame read failed")
                    break
                height, width = frame.shape[:2]
                sequence = len(rows)
                last_ms, clock = frame_offset_ms(
                    capture, args.camera is not None, fps, origin, sequence, last_ms
                )
                clock_sources.add(clock)

                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                inference_start = perf_counter()
                result = landmarker.detect_for_video(image, last_ms)
                inference_ms = (perf_counter() - inference_start) * 1000

                points = None
                if result.face_landmarks:
                    points = np.array([(p.x * width, p.y * height)
                                       for p in result.face_landmarks[0]])
                jitter = None
                if points is not None and previous_points is not None:
                    jitter = float(np.sqrt(np.mean(np.sum((points - previous_points) ** 2, axis=1))))
                previous_points = points
                angles = ()
                if result.facial_transformation_matrixes:
                    angles = pose_angles(result.facial_transformation_matrixes[0])

                if args.preview or args.save_video:
                    draw_overlay(frame, points, angles)
                if args.save_video:
                    if writer is None:
                        writer = cv2.VideoWriter(str(args.output / "overlay.mp4"),
                                                 cv2.VideoWriter_fourcc(*"mp4v"),
                                                 fps, (width, height))
                        if not writer.isOpened():
                            raise ValueError("Could not open MP4 overlay writer")
                    writer.write(frame)
                stop = False
                if args.preview:
                    cv2.imshow("T03 - Face Landmarker (q to quit)", frame)
                    stop = cv2.waitKey(1) & 0xFF in (ord("q"), 27)
                pipeline_ms = (perf_counter() - frame_start) * 1000
                rows.append((sequence, last_ms, 0 if points is None else len(points),
                             *(angles or (None, None, None)), jitter, inference_ms, pipeline_ms))
                if stop:
                    break
    finally:
        capture.release()
        if writer is not None:
            writer.release()
        if args.preview:
            cv2.destroyAllWindows()

    if not rows:
        raise ValueError("No decodable frames in the input")
    measured = rows[args.warmup:]
    jitter = [row[6] for row in measured[1:] if row[6] is not None]
    inference = [row[7] for row in measured]
    pipeline = [row[8] for row in measured]
    summary = {
        "source": "video" if args.video is not None else "webcam",
        "capture_backend": backend,
        "clock_sources": sorted(clock_sources),
        "width": width,
        "height": height,
        "input_fps": fps,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "mediapipe": mp.__version__,
        "opencv": cv2.__version__,
        "numpy": np.__version__,
        "model_sha256": hashlib.sha256(args.model.read_bytes()).hexdigest(),
        "overlay_saved": args.save_video,
        "preview": args.preview,
        "total_frames": len(rows),
        "warmup_frames_excluded": min(len(rows), args.warmup),
        "measured_frames": len(measured),
        "landmark_frames": sum(row[2] > 0 for row in measured),
        "pose_frames": sum(row[3] is not None for row in measured),
        "inference_fps": len(inference) * 1000 / sum(inference) if inference else None,
        "pipeline_fps": len(pipeline) * 1000 / sum(pipeline) if pipeline else None,
        "inference_p95_ms": float(np.percentile(inference, 95)) if inference else None,
        "jitter_pairs": len(jitter),
        "jitter_median_px": float(np.median(jitter)) if jitter else None,
        "jitter_p95_px": float(np.percentile(jitter, 95)) if jitter else None,
    }
    with (args.output / "frames.csv").open("w", newline="", encoding="utf-8") as log:
        csv.writer(log).writerow(("sequence", "offset_ms", "landmark_count", "pose_x_deg",
                                  "pose_y_deg", "pose_z_deg", "landmark_delta_rms_px",
                                  "inference_ms", "pipeline_ms"))
        csv.writer(log).writerows(rows)
    report = json.dumps(summary, indent=2, allow_nan=False)
    (args.output / "benchmark.json").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    try:
        run(parse_args())
    except (OSError, ValueError, RuntimeError) as exc:
        raise SystemExit(str(exc)) from exc
