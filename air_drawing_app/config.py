from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AppState(str, Enum):
    COLOR_SELECTION = "COLOR_SELECTION"
    DRAWING = "DRAWING"
    CLEARING = "CLEARING"
    NO_HAND = "NO_HAND"


@dataclass(frozen=True)
class ColorOption:
    name: str
    bgr: tuple[int, int, int]


COLORS: tuple[ColorOption, ...] = (
    ColorOption("RED", (40, 40, 235)),
    ColorOption("ORANGE", (35, 135, 245)),
    ColorOption("YELLOW", (35, 220, 245)),
    ColorOption("GREEN", (70, 205, 70)),
    ColorOption("CYAN", (220, 215, 35)),
    ColorOption("BLUE", (235, 110, 55)),
    ColorOption("PURPLE", (205, 80, 190)),
    ColorOption("PINK", (210, 80, 245)),
    ColorOption("WHITE", (245, 245, 245)),
    ColorOption("BLACK", (20, 20, 20)),
)


BRUSH_SIZES: tuple[int, ...] = (3, 6, 8, 10, 15, 25)
DEFAULT_BRUSH_SIZE = 8

WINDOW_NAME = "Hand Tracking Air Drawing"
CAMERA_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

SMOOTHING_ALPHA = 0.38
JUMP_DISTANCE_PX = 135
DRAWING_RESUME_FRAMES = 3

FIVE_FINGER_CONFIRM_FRAMES = 10
CLEAR_COOLDOWN_FRAMES = 28
POST_SELECTION_SKIP_FRAMES = 8
POST_BRUSH_SKIP_FRAMES = 4

STATUS_MESSAGE_FRAMES = 70
