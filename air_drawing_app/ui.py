from __future__ import annotations

import cv2
import numpy as np

from air_drawing_app.config import BRUSH_SIZES, COLORS, AppState, ColorOption


Rect = tuple[int, int, int, int]


class AirDrawingUI:
    def __init__(self) -> None:
        self.palette_rects: list[tuple[ColorOption, Rect]] = []
        self.brush_rects: list[tuple[int, Rect]] = []

    def layout(self, width: int, height: int) -> None:
        margin = 16
        color_size = max(42, min(58, (width - margin * 2 - 9 * 8) // 10))
        gap = 8
        start_x = max(margin, (width - (len(COLORS) * color_size + (len(COLORS) - 1) * gap)) // 2)
        y = 16
        self.palette_rects = []
        for index, color in enumerate(COLORS):
            x = start_x + index * (color_size + gap)
            self.palette_rects.append((color, (x, y, color_size, color_size)))

        brush_y = y + color_size + 12
        brush_width = 54
        brush_height = 34
        total_width = len(BRUSH_SIZES) * brush_width + (len(BRUSH_SIZES) - 1) * gap
        brush_x = max(margin, (width - total_width) // 2)
        self.brush_rects = []
        for index, size in enumerate(BRUSH_SIZES):
            x = brush_x + index * (brush_width + gap)
            self.brush_rects.append((size, (x, brush_y, brush_width, brush_height)))

    def hit_color(self, point: tuple[int, int]) -> ColorOption | None:
        return self._hit_test(point, self.palette_rects)

    def hit_brush(self, point: tuple[int, int]) -> int | None:
        return self._hit_test(point, self.brush_rects)

    @staticmethod
    def _hit_test(point: tuple[int, int], items):
        px, py = point
        for value, (x, y, w, h) in items:
            if x <= px <= x + w and y <= py <= y + h:
                return value
        return None

    def point_is_in_controls(self, point: tuple[int, int]) -> bool:
        return self.hit_color(point) is not None or self.hit_brush(point) is not None

    def draw(
        self,
        frame: np.ndarray,
        state: AppState,
        selected_color: ColorOption | None,
        brush_size: int,
        fps: float,
        cursor_point: tuple[int, int] | None,
        hovered_color: ColorOption | None,
        hovered_brush: int | None,
        message: str | None,
        multiple_hands: bool,
    ) -> np.ndarray:
        height, width = frame.shape[:2]
        self.layout(width, height)

        output = frame.copy()
        self._draw_top_panel(output)
        self._draw_palette(output, selected_color, hovered_color)
        self._draw_brushes(output, brush_size, hovered_brush)
        self._draw_status(output, state, selected_color, brush_size, fps, multiple_hands)

        if message:
            self._draw_notification(output, message)

        if cursor_point:
            cursor_color = selected_color.bgr if selected_color else (225, 225, 225)
            cv2.circle(output, cursor_point, max(7, brush_size // 2 + 4), cursor_color, 2, cv2.LINE_AA)
            cv2.circle(output, cursor_point, 3, cursor_color, -1, cv2.LINE_AA)

        return output

    def _draw_top_panel(self, frame: np.ndarray) -> None:
        overlay = frame.copy()
        height, width = frame.shape[:2]
        panel_height = min(132, height // 4)
        cv2.rectangle(overlay, (0, 0), (width, panel_height), (18, 20, 24), -1)
        cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

    def _draw_palette(
        self,
        frame: np.ndarray,
        selected_color: ColorOption | None,
        hovered_color: ColorOption | None,
    ) -> None:
        for color, rect in self.palette_rects:
            x, y, w, h = rect
            is_selected = selected_color is not None and color.name == selected_color.name
            is_hovered = hovered_color is not None and color.name == hovered_color.name
            border = (255, 255, 255) if is_selected else (150, 160, 172)
            thickness = 4 if is_selected or is_hovered else 2
            self._rounded_rect(frame, rect, color.bgr, radius=10, fill=True)
            self._rounded_rect(frame, rect, border, radius=10, thickness=thickness)
            label_color = (245, 245, 245) if color.name != "WHITE" else (25, 25, 25)
            short_name = color.name[:3]
            text_size = cv2.getTextSize(short_name, cv2.FONT_HERSHEY_SIMPLEX, 0.43, 1)[0]
            cv2.putText(
                frame,
                short_name,
                (x + (w - text_size[0]) // 2, y + h - 9),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.43,
                label_color,
                1,
                cv2.LINE_AA,
            )

    def _draw_brushes(self, frame: np.ndarray, brush_size: int, hovered_brush: int | None) -> None:
        for size, rect in self.brush_rects:
            selected = size == brush_size
            hovered = hovered_brush == size
            fill = (58, 64, 74) if not selected else (76, 96, 122)
            border = (235, 235, 235) if selected or hovered else (135, 145, 158)
            self._rounded_rect(frame, rect, fill, radius=9, fill=True)
            self._rounded_rect(frame, rect, border, radius=9, thickness=2)
            x, y, w, h = rect
            cv2.circle(frame, (x + 17, y + h // 2), max(2, min(size // 2, 9)), (245, 245, 245), -1, cv2.LINE_AA)
            label = f"{size}px"
            cv2.putText(frame, label, (x + 29, y + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (245, 245, 245), 1, cv2.LINE_AA)

    def _draw_status(
        self,
        frame: np.ndarray,
        state: AppState,
        selected_color: ColorOption | None,
        brush_size: int,
        fps: float,
        multiple_hands: bool,
    ) -> None:
        height, width = frame.shape[:2]
        status = [
            f"MODE: {state.value}",
            f"COLOR: {selected_color.name if selected_color else 'SELECT'}",
            f"BRUSH: {brush_size}px",
            f"FPS: {fps:04.1f}",
        ]
        text = "   ".join(status)
        x, y = 18, height - 22
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.64, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.64, (245, 245, 245), 1, cv2.LINE_AA)

        if multiple_hands:
            warning = "Show one hand"
            text_size = cv2.getTextSize(warning, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            box = (width - text_size[0] - 38, height - 58, text_size[0] + 22, 36)
            self._rounded_rect(frame, box, (45, 45, 55), radius=9, fill=True)
            cv2.putText(
                frame,
                warning,
                (box[0] + 11, box[1] + 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (80, 210, 255),
                2,
                cv2.LINE_AA,
            )

    def _draw_notification(self, frame: np.ndarray, message: str) -> None:
        height, width = frame.shape[:2]
        text_size = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
        box_w = text_size[0] + 42
        box_h = 52
        x = (width - box_w) // 2
        y = max(145, height // 5)
        self._rounded_rect(frame, (x, y, box_w, box_h), (25, 30, 36), radius=14, fill=True)
        self._rounded_rect(frame, (x, y, box_w, box_h), (220, 235, 245), radius=14, thickness=2)
        cv2.putText(
            frame,
            message,
            (x + 21, y + 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (245, 245, 245),
            2,
            cv2.LINE_AA,
        )

    @staticmethod
    def _rounded_rect(
        frame: np.ndarray,
        rect: Rect,
        color: tuple[int, int, int],
        radius: int = 8,
        thickness: int = 1,
        fill: bool = False,
    ) -> None:
        x, y, w, h = rect
        radius = min(radius, w // 2, h // 2)
        line_thickness = -1 if fill else thickness

        cv2.rectangle(frame, (x + radius, y), (x + w - radius, y + h), color, line_thickness)
        cv2.rectangle(frame, (x, y + radius), (x + w, y + h - radius), color, line_thickness)
        cv2.circle(frame, (x + radius, y + radius), radius, color, line_thickness, cv2.LINE_AA)
        cv2.circle(frame, (x + w - radius, y + radius), radius, color, line_thickness, cv2.LINE_AA)
        cv2.circle(frame, (x + radius, y + h - radius), radius, color, line_thickness, cv2.LINE_AA)
        cv2.circle(frame, (x + w - radius, y + h - radius), radius, color, line_thickness, cv2.LINE_AA)
