from __future__ import annotations

import cv2
import numpy as np


class DrawingCanvas:
    """Transparent BGRA layer used for persistent strokes."""

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.layer = np.zeros((height, width, 4), dtype=np.uint8)

    def ensure_size(self, width: int, height: int) -> None:
        if width == self.width and height == self.height:
            return
        self.width = width
        self.height = height
        self.layer = np.zeros((height, width, 4), dtype=np.uint8)

    def draw_line(
        self,
        start: tuple[int, int],
        end: tuple[int, int],
        color_bgr: tuple[int, int, int],
        brush_size: int,
    ) -> None:
        color_bgra = (*color_bgr, 255)
        cv2.line(self.layer, start, end, color_bgra, brush_size, cv2.LINE_AA)

    def clear(self) -> None:
        self.layer.fill(0)

    def composite(self, frame_bgr: np.ndarray) -> np.ndarray:
        if self.layer.shape[:2] != frame_bgr.shape[:2]:
            self.ensure_size(frame_bgr.shape[1], frame_bgr.shape[0])

        alpha = self.layer[:, :, 3:4].astype(np.float32) / 255.0
        canvas_rgb = self.layer[:, :, :3].astype(np.float32)
        frame = frame_bgr.astype(np.float32)
        blended = canvas_rgb * alpha + frame * (1.0 - alpha)
        return blended.astype(np.uint8)
