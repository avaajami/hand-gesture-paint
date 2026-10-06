from __future__ import annotations

from dataclasses import dataclass

import cv2
import mediapipe as mp
import numpy as np

from air_drawing_app.gesture_detector import LandmarkPoint

try:
    mp_hands_module = mp.solutions.hands
except AttributeError:
    from mediapipe.python.solutions import hands as mp_hands_module


@dataclass(frozen=True)
class HandDetection:
    landmarks: list[LandmarkPoint]
    handedness: str
    multiple_hands: bool


class HandTracker:
    """Thin wrapper around MediaPipe Hands."""

    def __init__(
        self,
        max_num_hands: int = 2,
        min_detection_confidence: float = 0.65,
        min_tracking_confidence: float = 0.55,
    ) -> None:
        self.mp_hands = mp_hands_module
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            model_complexity=1,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    def detect(self, frame_bgr: np.ndarray) -> HandDetection | None:
        height, width = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        results = self.hands.process(rgb)

        if not results.multi_hand_landmarks:
            return None

        first_hand = results.multi_hand_landmarks[0]
        handedness = "Unknown"
        if results.multi_handedness:
            handedness = results.multi_handedness[0].classification[0].label

        landmarks = [
            LandmarkPoint(
                x=min(max(int(point.x * width), 0), width - 1),
                y=min(max(int(point.y * height), 0), height - 1),
                z=point.z,
            )
            for point in first_hand.landmark
        ]
        return HandDetection(
            landmarks=landmarks,
            handedness=handedness,
            multiple_hands=len(results.multi_hand_landmarks) > 1,
        )

    def close(self) -> None:
        self.hands.close()
