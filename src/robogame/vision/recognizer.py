from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import cv2
import mediapipe as mp
import numpy as np


@dataclass(frozen=True)
class GestureDetection:
    """A single hand gesture prediction."""

    name: str
    score: float
    handedness: str | None = None


class GestureRecognitionModel:
    """Small wrapper around MediaPipe GestureRecognizer.

    MediaPipe expects RGB images, while OpenCV captures BGR images. This class
    keeps that conversion in one place so the rest of the app can pass OpenCV
    frames directly.
    """

    def __init__(
        self,
        model_path: str | Path,
        *,
        running_mode: str = "image",
        num_hands: int = 1,
        min_hand_detection_confidence: float = 0.5,
        min_hand_presence_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(f"model file not found: {self.model_path}")

        vision = mp.tasks.vision
        mode_name = running_mode.strip().upper()
        if mode_name == "VIDEO":
            mode = vision.RunningMode.VIDEO
        elif mode_name == "IMAGE":
            mode = vision.RunningMode.IMAGE
        else:
            raise ValueError("running_mode must be 'image' or 'video'")

        options = vision.GestureRecognizerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(self.model_path)),
            running_mode=mode,
            num_hands=num_hands,
            min_hand_detection_confidence=min_hand_detection_confidence,
            min_hand_presence_confidence=min_hand_presence_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._running_mode = mode_name
        self._recognizer = vision.GestureRecognizer.create_from_options(options)

    def close(self) -> None:
        self._recognizer.close()

    def __enter__(self) -> GestureRecognitionModel:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:  # type: ignore[no-untyped-def]
        self.close()

    def recognize_bgr(self, frame_bgr: np.ndarray, *, timestamp_ms: int | None = None):
        image = self._to_mediapipe_image(frame_bgr)
        if self._running_mode == "VIDEO":
            if timestamp_ms is None:
                raise ValueError("timestamp_ms is required in video mode")
            return self._recognizer.recognize_for_video(image, timestamp_ms)
        return self._recognizer.recognize(image)

    def detect_bgr(
        self,
        frame_bgr: np.ndarray,
        *,
        timestamp_ms: int | None = None,
    ) -> list[GestureDetection]:
        result = self.recognize_bgr(frame_bgr, timestamp_ms=timestamp_ms)
        return list(self._detections_from_result(result))

    @staticmethod
    def draw_result(frame_bgr: np.ndarray, detections: Iterable[GestureDetection]) -> np.ndarray:
        output = frame_bgr.copy()
        y = 32
        for detection in detections:
            text = f"{detection.name} {detection.score:.2f}"
            if detection.handedness:
                text = f"{detection.handedness}: {text}"
            cv2.putText(
                output,
                text,
                (16, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
                cv2.LINE_AA,
            )
            y += 32
        return output

    @staticmethod
    def _to_mediapipe_image(frame_bgr: np.ndarray):
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        return mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    @staticmethod
    def _detections_from_result(result) -> Iterable[GestureDetection]:  # type: ignore[no-untyped-def]
        handedness_list = getattr(result, "handedness", []) or []
        for index, gesture_categories in enumerate(getattr(result, "gestures", []) or []):
            if not gesture_categories:
                continue
            top_gesture = gesture_categories[0]
            handedness = None
            if index < len(handedness_list) and handedness_list[index]:
                handedness = handedness_list[index][0].category_name
            yield GestureDetection(
                name=top_gesture.category_name,
                score=float(top_gesture.score),
                handedness=handedness,
            )
