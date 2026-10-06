from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from typing import Sequence


@dataclass(frozen=True)
class LandmarkPoint:
    x: int
    y: int
    z: float = 0.0


@dataclass(frozen=True)
class FingerStates:
    thumb: bool
    index: bool
    middle: bool
    ring: bool
    pinky: bool

    @property
    def all_open(self) -> bool:
        return self.thumb and self.index and self.middle and self.ring and self.pinky


WRIST = 0
THUMB_IP = 3
THUMB_TIP = 4
INDEX_MCP = 5
INDEX_PIP = 6
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_PIP = 10
MIDDLE_TIP = 12
RING_PIP = 14
RING_TIP = 16
PINKY_PIP = 18
PINKY_TIP = 20


def distance(a: LandmarkPoint, b: LandmarkPoint) -> float:
    return hypot(a.x - b.x, a.y - b.y)


def _hand_scale(landmarks: Sequence[LandmarkPoint]) -> float:
    xs = [point.x for point in landmarks]
    ys = [point.y for point in landmarks]
    bbox = hypot(max(xs) - min(xs), max(ys) - min(ys))
    wrist_to_middle = distance(landmarks[WRIST], landmarks[MIDDLE_MCP])
    return max(bbox, wrist_to_middle, 1.0)


def _finger_extended(
    landmarks: Sequence[LandmarkPoint],
    tip_id: int,
    pip_id: int,
    scale: float,
) -> bool:
    tip = landmarks[tip_id]
    pip = landmarks[pip_id]
    wrist = landmarks[WRIST]
    vertical_margin = 0.035 * scale
    return tip.y < pip.y - vertical_margin and distance(tip, wrist) > distance(pip, wrist)


def is_index_up(landmarks: Sequence[LandmarkPoint]) -> bool:
    return _finger_extended(landmarks, INDEX_TIP, INDEX_PIP, _hand_scale(landmarks))


def is_middle_up(landmarks: Sequence[LandmarkPoint]) -> bool:
    return _finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP, _hand_scale(landmarks))


def is_ring_up(landmarks: Sequence[LandmarkPoint]) -> bool:
    return _finger_extended(landmarks, RING_TIP, RING_PIP, _hand_scale(landmarks))


def is_pinky_up(landmarks: Sequence[LandmarkPoint]) -> bool:
    return _finger_extended(landmarks, PINKY_TIP, PINKY_PIP, _hand_scale(landmarks))


def is_thumb_up(landmarks: Sequence[LandmarkPoint]) -> bool:
    scale = _hand_scale(landmarks)
    thumb_tip = landmarks[THUMB_TIP]
    thumb_ip = landmarks[THUMB_IP]
    wrist = landmarks[WRIST]
    index_mcp = landmarks[INDEX_MCP]

    thumb_spread = distance(thumb_tip, index_mcp) > 0.22 * scale
    thumb_extended = distance(thumb_tip, wrist) > distance(thumb_ip, wrist) + 0.04 * scale
    return thumb_spread and thumb_extended


def get_finger_states(landmarks: Sequence[LandmarkPoint]) -> FingerStates:
    return FingerStates(
        thumb=is_thumb_up(landmarks),
        index=is_index_up(landmarks),
        middle=is_middle_up(landmarks),
        ring=is_ring_up(landmarks),
        pinky=is_pinky_up(landmarks),
    )


def five_finger_gesture_detected(landmarks: Sequence[LandmarkPoint]) -> bool:
    return get_finger_states(landmarks).all_open
