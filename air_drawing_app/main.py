from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from math import hypot

import cv2

from air_drawing_app.config import (
    BRUSH_SIZES,
    CAMERA_INDEX,
    CLEAR_COOLDOWN_FRAMES,
    DEFAULT_BRUSH_SIZE,
    DRAWING_RESUME_FRAMES,
    FIVE_FINGER_CONFIRM_FRAMES,
    FRAME_HEIGHT,
    FRAME_WIDTH,
    JUMP_DISTANCE_PX,
    POST_BRUSH_SKIP_FRAMES,
    POST_SELECTION_SKIP_FRAMES,
    SMOOTHING_ALPHA,
    STATUS_MESSAGE_FRAMES,
    WINDOW_NAME,
    AppState,
    ColorOption,
)
from air_drawing_app.drawing_canvas import DrawingCanvas
from air_drawing_app.gesture_detector import INDEX_TIP, five_finger_gesture_detected, is_index_up
from air_drawing_app.hand_tracker import HandTracker
from air_drawing_app.ui import AirDrawingUI


@dataclass
class SmoothedPoint:
    point: tuple[int, int]
    stable: bool


class PointSmoother:
    def __init__(self, alpha: float, jump_distance_px: int) -> None:
        self.alpha = alpha
        self.jump_distance_px = jump_distance_px
        self.current: tuple[float, float] | None = None
        self.stable_frames = 0

    def update(self, point: tuple[int, int]) -> SmoothedPoint:
        if self.current is None:
            self.current = (float(point[0]), float(point[1]))
            self.stable_frames = 1
            return SmoothedPoint(point, stable=False)

        distance = hypot(point[0] - self.current[0], point[1] - self.current[1])
        if distance > self.jump_distance_px:
            self.current = (float(point[0]), float(point[1]))
            self.stable_frames = 0
            return SmoothedPoint(point, stable=False)

        x = self.alpha * point[0] + (1.0 - self.alpha) * self.current[0]
        y = self.alpha * point[1] + (1.0 - self.alpha) * self.current[1]
        self.current = (x, y)
        self.stable_frames += 1
        return SmoothedPoint((int(x), int(y)), stable=self.stable_frames >= DRAWING_RESUME_FRAMES)

    def reset(self) -> None:
        self.current = None
        self.stable_frames = 0


def open_camera() -> cv2.VideoCapture:
    camera = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    if not camera.isOpened():
        camera = cv2.VideoCapture(CAMERA_INDEX)

    if not camera.isOpened():
        raise RuntimeError("Could not open webcam. Check that a camera is connected and not used by another app.")

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    return camera


def clamp_brush_index(current_size: int, offset: int) -> int:
    closest = min(range(len(BRUSH_SIZES)), key=lambda index: abs(BRUSH_SIZES[index] - current_size))
    next_index = min(max(closest + offset, 0), len(BRUSH_SIZES) - 1)
    return BRUSH_SIZES[next_index]


def main() -> None:
    try:
        camera = open_camera()
    except RuntimeError as error:
        print(error)
        sys.exit(1)

    try:
        tracker = HandTracker()
    except Exception as error:
        camera.release()
        print(f"Could not initialize MediaPipe Hands: {error}")
        sys.exit(1)

    ui = AirDrawingUI()
    canvas: DrawingCanvas | None = None
    smoother = PointSmoother(SMOOTHING_ALPHA, JUMP_DISTANCE_PX)

    selected_color: ColorOption | None = None
    brush_size = DEFAULT_BRUSH_SIZE
    state = AppState.COLOR_SELECTION
    previous_active_state = AppState.COLOR_SELECTION

    previous_draw_point: tuple[int, int] | None = None
    five_finger_count = 0
    clear_cooldown = 0
    drawing_skip_frames = 0
    message: str | None = "Select a Color"
    message_frames = STATUS_MESSAGE_FRAMES

    last_time = time.perf_counter()
    fps = 0.0

    try:
        while True:
            ok, frame = camera.read()
            if not ok:
                print("Could not read a frame from the webcam.")
                break

            frame = cv2.flip(frame, 1)
            height, width = frame.shape[:2]
            ui.layout(width, height)
            if canvas is None:
                canvas = DrawingCanvas(width, height)
            else:
                canvas.ensure_size(width, height)

            now = time.perf_counter()
            elapsed = max(now - last_time, 1e-6)
            last_time = now
            fps = fps * 0.85 + (1.0 / elapsed) * 0.15 if fps else 1.0 / elapsed

            detection = tracker.detect(frame)
            hovered_color = None
            hovered_brush = None
            cursor_point = None
            multiple_hands = False

            if clear_cooldown > 0:
                clear_cooldown -= 1
            if drawing_skip_frames > 0:
                drawing_skip_frames -= 1
            if message_frames > 0:
                message_frames -= 1
                if message_frames == 0:
                    message = None

            if detection is None:
                if state != AppState.NO_HAND:
                    previous_active_state = state
                state = AppState.NO_HAND
                smoother.reset()
                previous_draw_point = None
                five_finger_count = 0
            else:
                multiple_hands = detection.multiple_hands
                if state == AppState.NO_HAND:
                    state = previous_active_state

                index_point_raw = detection.landmarks[INDEX_TIP]
                smoothed = smoother.update((index_point_raw.x, index_point_raw.y))
                cursor_point = smoothed.point

                five_fingers_open = five_finger_gesture_detected(detection.landmarks)
                if five_fingers_open:
                    five_finger_count += 1
                else:
                    five_finger_count = 0

                if (
                    five_finger_count >= FIVE_FINGER_CONFIRM_FRAMES
                    and clear_cooldown == 0
                ):
                    state = AppState.CLEARING
                    canvas.clear()
                    selected_color = None
                    previous_draw_point = None
                    smoother.reset()
                    five_finger_count = 0
                    clear_cooldown = CLEAR_COOLDOWN_FRAMES
                    drawing_skip_frames = POST_SELECTION_SKIP_FRAMES
                    state = AppState.COLOR_SELECTION
                    previous_active_state = state
                    message = "Canvas Cleared - Select a Color"
                    message_frames = STATUS_MESSAGE_FRAMES

                hovered_brush = ui.hit_brush(cursor_point)
                if hovered_brush is not None:
                    if hovered_brush != brush_size:
                        brush_size = hovered_brush
                        message = f"Brush {brush_size}px"
                        message_frames = 28
                    previous_draw_point = None
                    drawing_skip_frames = max(drawing_skip_frames, POST_BRUSH_SKIP_FRAMES)

                if state == AppState.COLOR_SELECTION and cursor_point is not None:
                    hovered_color = ui.hit_color(cursor_point)
                    if hovered_color is not None:
                        selected_color = hovered_color
                        state = AppState.DRAWING
                        previous_active_state = state
                        previous_draw_point = None
                        drawing_skip_frames = POST_SELECTION_SKIP_FRAMES
                        message = f"Color {selected_color.name}"
                        message_frames = 32

                index_is_up = is_index_up(detection.landmarks)
                can_draw = (
                    state == AppState.DRAWING
                    and selected_color is not None
                    and index_is_up
                    and smoothed.stable
                    and not five_fingers_open
                    and clear_cooldown == 0
                    and drawing_skip_frames == 0
                    and not ui.point_is_in_controls(cursor_point)
                )

                if can_draw:
                    if previous_draw_point is not None:
                        canvas.draw_line(previous_draw_point, cursor_point, selected_color.bgr, brush_size)
                    previous_draw_point = cursor_point
                else:
                    previous_draw_point = None

            composed = canvas.composite(frame) if canvas else frame
            display = ui.draw(
                composed,
                state,
                selected_color,
                brush_size,
                fps,
                cursor_point,
                hovered_color,
                hovered_brush,
                message,
                multiple_hands,
            )

            cv2.imshow(WINDOW_NAME, display)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:
                break
            if key in (ord("c"), ord("C")) and canvas is not None:
                canvas.clear()
                selected_color = None
                state = AppState.COLOR_SELECTION
                previous_active_state = state
                previous_draw_point = None
                smoother.reset()
                message = "Canvas Cleared - Select a Color"
                message_frames = STATUS_MESSAGE_FRAMES
            elif key in (ord("r"), ord("R")):
                selected_color = None
                state = AppState.COLOR_SELECTION
                previous_active_state = state
                previous_draw_point = None
                smoother.reset()
                message = "Select a Color"
                message_frames = STATUS_MESSAGE_FRAMES
            elif key in (ord("+"), ord("=")):
                brush_size = clamp_brush_index(brush_size, 1)
                message = f"Brush {brush_size}px"
                message_frames = 28
            elif key in (ord("-"), ord("_")):
                brush_size = clamp_brush_index(brush_size, -1)
                message = f"Brush {brush_size}px"
                message_frames = 28
    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
