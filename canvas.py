"""
canvas.py
---------
Owns the drawing surface: strokes, erasing, undo/redo history,
optional shape correction, saving to PNG, and compositing onto
the live camera frame.
"""

import os
import time

import cv2
import numpy as np

import config
from shape_utils import correct_shape, render_shape


class Canvas:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.canvas = np.zeros((height, width, 3), dtype=np.uint8)

        self.undo_stack = []
        self.redo_stack = []

        self.prev_point = None
        self.current_stroke = []       # points collected during the active stroke
        self.shape_mode = False        # bonus: auto shape-correction toggle

        self._last_color = config.COLORS[config.DEFAULT_COLOR]
        self._last_thickness = config.BRUSH_THICKNESS_DEFAULT

    # ---------- history ----------
    def _push_undo(self):
        self.undo_stack.append(self.canvas.copy())
        if len(self.undo_stack) > config.MAX_UNDO_STEPS:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.canvas.copy())
            self.canvas = self.undo_stack.pop()
            self.prev_point = None

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.canvas.copy())
            self.canvas = self.redo_stack.pop()
            self.prev_point = None

    # ---------- strokes ----------
    def start_stroke(self):
        self._push_undo()
        self.prev_point = None
        self.current_stroke = []

    def draw_line(self, point, color, thickness):
        self._last_color, self._last_thickness = color, thickness
        if self.prev_point is not None:
            cv2.line(self.canvas, self.prev_point, point, color, thickness, lineType=cv2.LINE_AA)
        else:
            cv2.circle(self.canvas, point, max(thickness // 2, 1), color, -1, lineType=cv2.LINE_AA)
        self.prev_point = point
        self.current_stroke.append(point)

    def erase(self, point, thickness):
        if self.prev_point is not None:
            cv2.line(self.canvas, self.prev_point, point, (0, 0, 0), thickness, lineType=cv2.LINE_AA)
        else:
            cv2.circle(self.canvas, point, max(thickness // 2, 1), (0, 0, 0), -1)
        self.prev_point = point

    def end_stroke(self):
        if self.shape_mode and len(self.current_stroke) > 5:
            # Roll back to the pre-stroke snapshot, then draw the corrected shape on top.
            base = self.undo_stack[-1] if self.undo_stack else self.canvas
            self.canvas = base.copy()
            shape = correct_shape(self.current_stroke, self._last_color, self._last_thickness)
            render_shape(self.canvas, shape)
        self.prev_point = None
        self.current_stroke = []

    def clear(self):
        self._push_undo()
        self.canvas[:] = 0
        self.prev_point = None
        self.current_stroke = []

    # ---------- persistence ----------
    def save(self, output_dir=config.OUTPUT_DIR):
        os.makedirs(output_dir, exist_ok=True)
        filename = f"whiteboard_{time.strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(output_dir, filename)
        cv2.imwrite(filepath, self.canvas)
        return filepath

    # ---------- compositing ----------
    def overlay_on(self, frame):
        """Blend the drawing on top of the live camera frame (transparent background)."""
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 10, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)
        bg = cv2.bitwise_and(frame, frame, mask=mask_inv)
        fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
        return cv2.add(bg, fg)