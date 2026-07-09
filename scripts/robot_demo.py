from __future__ import annotations

import argparse
import logging
import os
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import yaml

from robogame.display.player import DEFAULT_EXPRESSIONS_DIR, discover_expressions
from robogame.display.web_player import set_remote_expression
from robogame.vision import GestureDetection, GestureRecognitionModel


LOGGER = logging.getLogger("robot_demo")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOUNDS_DIR = PROJECT_ROOT / "assets" / "sounds"

GESTURE_ALIASES = {
    "openpalm": "open_palm",
    "open_palm": "open_palm",
    "closedfist": "fist",
    "closed_fist": "fist",
    "fist": "fist",
    "victory": "victory",
    "thumbup": "thumb_up",
    "thumb_up": "thumb_up",
    "thumbdown": "thumb_down",
    "thumb_down": "thumb_down",
    "iloveyou": "iloveyou",
    "i_love_you": "iloveyou",
    "pointingup": "pointing_up",
    "pointing_up": "pointing_up",
}


@dataclass(frozen=True)
class GestureAction:
    key: str
    expression: str | None = None
    sound: Path | None = None


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def normalize_gesture_name(name: str) -> str:
    normalized = name.strip().lower().replace("-", "_").replace(" ", "_")
    compact = normalized.replace("_", "")
    return GESTURE_ALIASES.get(normalized, GESTURE_ALIASES.get(compact, normalized))


def load_actions(path: Path, *, sounds_dir: Path) -> dict[str, GestureAction]:
    data = load_yaml(path)
    actions: dict[str, GestureAction] = {}
    for key, value in (data.get("gestures") or {}).items():
        if not isinstance(value, dict):
            continue
        expression = value.get("expression") or value.get("emotion")
        sound_name = value.get("sound")
        sound = sounds_dir / sound_name if sound_name else None
        actions[normalize_gesture_name(key)] = GestureAction(
            key=key,
            expression=expression,
            sound=sound,
        )
    return actions


def available_expression_names(expressions_dir: Path = DEFAULT_EXPRESSIONS_DIR) -> set[str]:
    return {asset.name for asset in discover_expressions(expressions_dir)}


class AudioManager:
    """Play WAV files without overlapping.

    Each new ``play`` call stops the previous player process before starting a
    new one, so rapid gesture triggers replace the audio instead of stacking.
    On Windows ``os.startfile`` is fire-and-forget and cannot be interrupted.
    """

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._lock = threading.Lock()

    def play(self, path: Path) -> None:
        if not path.exists():
            LOGGER.warning("sound not found: %s", path)
            return
        thread = threading.Thread(target=self._play_blocking, args=(path,), daemon=True)
        thread.start()

    def stop(self) -> None:
        with self._lock:
            self._stop_locked()

    def _play_blocking(self, path: Path) -> None:
        if sys.platform == "win32":
            try:
                os.startfile(str(path))  # type: ignore[attr-defined]
            except OSError as error:
                LOGGER.warning("could not play %s: %s", path, error)
            return

        player = shutil.which("aplay") or shutil.which("afplay") or shutil.which("paplay")
        if player is None:
            LOGGER.warning("no audio player found; install alsa-utils for aplay on Raspberry Pi")
            return

        with self._lock:
            self._stop_locked()
            try:
                proc = subprocess.Popen([player, str(path)])
            except OSError as error:
                LOGGER.warning("could not start %s: %s", player, error)
                return
            self._process = proc
        proc.wait()

    def _stop_locked(self) -> None:
        proc = self._process
        if proc is not None and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1)
            except subprocess.TimeoutExpired:
                proc.kill()
        self._process = None


def select_detection(detections: list[GestureDetection], min_score: float) -> GestureDetection | None:
    if not detections:
        return None
    detection = max(detections, key=lambda item: item.score)
    if detection.score < min_score:
        return None
    return detection


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the camera/audio/expression demo. Start scripts/test_display_web.py first."
    )
    parser.add_argument("--config", type=Path, default=PROJECT_ROOT / "config" / "robot.yaml")
    parser.add_argument("--gestures", type=Path, default=PROJECT_ROOT / "config" / "gestures.yaml")
    parser.add_argument("--model", type=Path, default=PROJECT_ROOT / "assets" / "models" / "gesture_recognizer.task")
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--mirror", action="store_true")
    parser.add_argument("--display-url", default="http://127.0.0.1:8765")
    parser.add_argument("--min-score", type=float, default=None)
    parser.add_argument("--cooldown", type=float, default=None)
    parser.add_argument("--idle-timeout", type=float, default=None)
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--no-audio", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    config = load_yaml(args.config)
    camera_config = config.get("camera") or {}
    width = args.width or int(camera_config.get("width", 640))
    height = args.height or int(camera_config.get("height", 480))

    interaction = config.get("interaction") or {}
    min_score = args.min_score if args.min_score is not None else float(interaction.get("min_score", 0.55))
    cooldown = args.cooldown if args.cooldown is not None else float(interaction.get("cooldown", 2.0))
    idle_timeout = args.idle_timeout if args.idle_timeout is not None else float(interaction.get("idle_timeout", 3.0))
    idle_expression = interaction.get("idle_expression")

    actions = load_actions(args.gestures, sounds_dir=DEFAULT_SOUNDS_DIR)
    if not actions:
        raise SystemExit(f"no gesture actions found in {args.gestures}")

    expression_names = available_expression_names()
    if idle_expression and idle_expression not in expression_names:
        LOGGER.warning("idle expression not found in assets/expressions: %s", idle_expression)
    for key, action in actions.items():
        if action.expression and action.expression not in expression_names:
            LOGGER.warning(
                "expression for gesture '%s' not found: %s (will not switch on screen)",
                key,
                action.expression,
            )
        if action.sound and not action.sound.exists():
            LOGGER.warning("sound for gesture '%s' not found: %s", key, action.sound)

    capture = cv2.VideoCapture(args.camera)
    if not capture.isOpened():
        raise RuntimeError(f"could not open camera: {args.camera}")
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    audio = AudioManager()
    last_triggered: dict[str, float] = {}
    last_action_time = 0.0
    current_expression: str | None = None
    start = time.perf_counter()
    LOGGER.info("loaded actions: %s", ", ".join(actions.keys()))
    LOGGER.info(
        "min_score=%.2f cooldown=%.2fs idle_timeout=%.2fs idle=%s",
        min_score,
        cooldown,
        idle_timeout,
        idle_expression,
    )
    LOGGER.info("press Ctrl+C%s to stop", ", or q in preview" if args.preview else "")

    try:
        with GestureRecognitionModel(args.model, running_mode="video") as model:
            while True:
                ok, frame = capture.read()
                if not ok:
                    LOGGER.warning("camera frame read failed")
                    continue
                if args.mirror:
                    frame = cv2.flip(frame, 1)
                frame = cv2.resize(frame, (width, height))

                timestamp_ms = int((time.perf_counter() - start) * 1000)
                detections = model.detect_bgr(frame, timestamp_ms=timestamp_ms)
                detection = select_detection(detections, min_score)
                now = time.monotonic()

                if detection is not None:
                    key = normalize_gesture_name(detection.name)
                    action = actions.get(key)
                    if action is not None and now - last_triggered.get(key, 0) >= cooldown:
                        LOGGER.info("gesture=%s score=%.2f action=%s", detection.name, detection.score, action.key)
                        if action.expression:
                            try:
                                set_remote_expression(action.expression, base_url=args.display_url)
                                current_expression = action.expression
                            except Exception as error:  # noqa: BLE001
                                LOGGER.warning("could not switch expression: %s", error)
                        if action.sound and not args.no_audio:
                            audio.play(action.sound)
                        last_triggered[key] = now
                        last_action_time = now

                if (
                    idle_expression
                    and now - last_action_time >= idle_timeout
                    and current_expression != idle_expression
                ):
                    try:
                        set_remote_expression(idle_expression, base_url=args.display_url)
                        current_expression = idle_expression
                    except Exception as error:  # noqa: BLE001
                        LOGGER.warning("could not switch to idle expression: %s", error)

                if args.preview:
                    output = model.draw_result(frame, detections)
                    cv2.imshow("robogame demo camera", output)
                    key_code = cv2.waitKey(1) & 0xFF
                    if key_code in (ord("q"), ord("Q"), 27):
                        break
    except KeyboardInterrupt:
        pass
    finally:
        audio.stop()
        capture.release()
        if args.preview:
            cv2.destroyAllWindows()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
