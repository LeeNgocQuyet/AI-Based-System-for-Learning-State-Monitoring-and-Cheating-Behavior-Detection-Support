"""Create a repeatable local test video from a user-supplied portrait."""

import argparse
from pathlib import Path

import cv2
import numpy as np


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("portrait", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.output.suffix.lower() != ".avi" or args.output.exists():
        parser.error("Output must be a new .avi file")
    image = cv2.imread(str(args.portrait))
    if image is None:
        parser.error("Could not read portrait")
    height, width = image.shape[:2]
    scale = min(640 / width, 480 / height)
    image = cv2.resize(image, (round(width * scale), round(height * scale)))
    height, width = image.shape[:2]
    portrait = np.zeros((480, 640, 3), dtype=np.uint8)
    x, y = (640 - width) // 2, (480 - height) // 2
    portrait[y:y + height, x:x + width] = image
    rotation = cv2.getRotationMatrix2D((320, 240), 15, 1)
    rotated = cv2.warpAffine(portrait, rotation, (640, 480))
    blank = np.zeros_like(portrait)
    writer = cv2.VideoWriter(str(args.output), cv2.VideoWriter_fourcc(*"MJPG"), 30, (640, 480))
    try:
        if not writer.isOpened():
            parser.error("Could not open MJPG video writer")
        for frame, count in ((portrait, 150), (blank, 30), (rotated, 60)):
            for _ in range(count):
                writer.write(frame)
    finally:
        writer.release()


if __name__ == "__main__":
    main()
