from __future__ import annotations

import argparse
import time
from pathlib import Path

import cv2

from robogame.vision import GestureRecognitionModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Test MediaPipe gesture recognition. In the preview window, press q or Esc to stop."
    )
    parser.add_argument("--model", default="assets/models/gesture_recognizer.task")
    parser.add_argument("--image", help="Path to a still image to recognize.")
    parser.add_argument("--video", help="Path to a video file to recognize.")
    parser.add_argument("--camera", type=int, help="Camera index, usually 0.")
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--max-frames", type=int, default=0, help="0 means no frame limit.")
    parser.add_argument("--mirror", action="store_true", help="Mirror camera frames.")
    parser.add_argument(
        "--save-frame",
        help="Save the first annotated frame with a detected gesture, then stop.",
    )
    parser.add_argument(
        "--warmup-frames",
        type=int,
        default=30,
        help="Skip this many camera/video frames before saving a detected frame.",
    )
    parser.add_argument(
        "--no-window",
        action="store_true",
        help="Print results only. Use Ctrl+C to stop an unlimited camera run.",
    )
    parser.add_argument("--save-output", help="Save the annotated image or video for reports.")
    return parser.parse_args()


def print_detections(prefix: str, detections) -> None:  # type: ignore[no-untyped-def]
    if not detections:
        print(f"{prefix}: no hand gesture detected")
        return
    summary = ", ".join(
        f"{item.handedness + ' ' if item.handedness else ''}{item.name}({item.score:.2f})"
        for item in detections
    )
    print(f"{prefix}: {summary}")


def prepare_output_path(path_value: str) -> Path:
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def run_image(args: argparse.Namespace) -> int:
    frame = cv2.imread(args.image)
    if frame is None:
        raise FileNotFoundError(f"could not read image: {args.image}")

    with GestureRecognitionModel(args.model, running_mode="image") as model:
        detections = model.detect_bgr(frame)
        print_detections(Path(args.image).name, detections)
        output = model.draw_result(frame, detections)

    if args.save_output:
        output_path = prepare_output_path(args.save_output)
        if not cv2.imwrite(str(output_path), output):
            raise RuntimeError(f"could not save annotated image: {output_path}")
        print(f"saved annotated image: {output_path}")
    if not args.no_window:
        cv2.imshow("robogame vision test", output)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    return 0


def run_video_source(args: argparse.Namespace, source: str | int) -> int:
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError(f"could not open video source: {source}")

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    writer = None
    saved_frame = False
    if args.save_output:
        output_path = prepare_output_path(args.save_output)
        fps = capture.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 1:
            fps = 30
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_path), fourcc, fps, (args.width, args.height))
        if not writer.isOpened():
            raise RuntimeError(f"could not save annotated video: {output_path}")

    frame_index = 0
    start = time.perf_counter()
    if not args.no_window:
        print("Preview window is open. Press q or Esc to stop.")

    with GestureRecognitionModel(args.model, running_mode="video") as model:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            if args.mirror:
                frame = cv2.flip(frame, 1)

            frame = cv2.resize(frame, (args.width, args.height))
            timestamp_ms = int((time.perf_counter() - start) * 1000)
            detections = model.detect_bgr(frame, timestamp_ms=timestamp_ms)

            if frame_index % 10 == 0:
                print_detections(f"frame {frame_index}", detections)

            output = model.draw_result(frame, detections)
            if (
                args.save_frame
                and not saved_frame
                and frame_index >= args.warmup_frames
                and detections
            ):
                frame_path = prepare_output_path(args.save_frame)
                if not cv2.imwrite(str(frame_path), output):
                    raise RuntimeError(f"could not save annotated frame: {frame_path}")
                print(f"saved annotated frame: {frame_path}")
                saved_frame = True
                if not args.save_output:
                    break

            if writer is not None:
                writer.write(output)
            if not args.no_window:
                cv2.imshow("robogame vision test", output)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q"), 27):
                    break

            frame_index += 1
            if args.max_frames and frame_index >= args.max_frames:
                break

    capture.release()
    if writer is not None:
        writer.release()
        print(f"saved annotated video: {output_path}")
    if not args.no_window:
        cv2.destroyAllWindows()
    return 0


def main() -> int:
    args = parse_args()
    selected_inputs = [args.image is not None, args.video is not None, args.camera is not None]
    if sum(selected_inputs) != 1:
        raise SystemExit("choose exactly one input: --image, --video, or --camera")

    if args.image:
        return run_image(args)
    if args.video:
        return run_video_source(args, args.video)
    return run_video_source(args, args.camera)


if __name__ == "__main__":
    raise SystemExit(main())
