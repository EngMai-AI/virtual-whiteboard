"""
toolbar.py
----------
Draws the on-screen toolbar and handles "hover to click" selection:
hold the SELECT gesture (index + middle fingers up) over a button for
config.DWELL_TIME_SEC seconds to activate it. This avoids needing a
"pinch/click" gesture, which is unreliable with a single camera.
"""

import time

import cv2

import config


class Button:
    def __init__(self, x, y, w, h, label, action, color=(60, 60, 60)):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.label = label
        self.action = action  # tuple: (kind, value)
        self.color = color

    def contains(self, px, py):
        return self.x <= px <= self.x + self.w and self.y <= py <= self.y + self.h

    def draw(self, frame, active=False, hover_progress=0.0):
        cv2.rectangle(frame, (self.x, self.y), (self.x + self.w, self.y + self.h), self.color, -1)
        if active:
            cv2.rectangle(frame, (self.x, self.y), (self.x + self.w, self.y + self.h), (255, 255, 255), 3)
        if hover_progress > 0:
            fill_w = int(self.w * hover_progress)
            cv2.rectangle(frame, (self.x, self.y + self.h - 5),
                          (self.x + fill_w, self.y + self.h), (0, 255, 0), -1)
        text_color = (255, 255, 255) if sum(self.color) < 400 else (0, 0, 0)
        cv2.putText(frame, self.label, (self.x + 6, self.y + self.h // 2 + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.48, text_color, 1, cv2.LINE_AA)


class Toolbar:
    def __init__(self, width, height=80):
        self.width = width
        self.height = height
        self.buttons = []
        self._build_buttons()
        self.hover_button = None
        self.hover_start = None

    def _build_buttons(self):
        x, y = 10, 10
        w, h = 90, 60
        gap = 8

        for name, bgr in config.COLORS.items():
            self.buttons.append(Button(x, y, w, h, name, ("color", name), color=bgr))
            x += w + gap

        extra = [
            ("Brush", ("tool", "brush")),
            ("Eraser", ("tool", "eraser")),
            ("Thick+", ("thickness", 1)),
            ("Thick-", ("thickness", -1)),
            ("Undo", ("history", "undo")),
            ("Redo", ("history", "redo")),
            ("Shapes", ("toggle", "shape_mode")),
            ("Clear", ("clear", None)),
            ("Save", ("save", None)),
        ]
        for label, action in extra:
            self.buttons.append(Button(x, y, w, h, label, action, color=(60, 60, 60)))
            x += w + gap

    def draw(self, frame, active_tool=None, active_color=None, shape_mode=False):
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (self.width, self.height), (30, 30, 30), -1)
        frame[:] = cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)

        for btn in self.buttons:
            is_active = False
            if btn.action[0] == "tool" and btn.action[1] == active_tool:
                is_active = True
            if btn.action[0] == "color" and btn.action[1] == active_color:
                is_active = True
            if btn.action == ("toggle", "shape_mode") and shape_mode:
                is_active = True

            hover_progress = 0.0
            if self.hover_button is btn and self.hover_start is not None:
                hover_progress = min((time.time() - self.hover_start) / config.DWELL_TIME_SEC, 1.0)

            btn.draw(frame, active=is_active, hover_progress=hover_progress)

    def update_hover(self, point):
        """
        Call every frame with the current SELECT-gesture fingertip position
        (or None if not in select mode). Returns the completed action tuple
        once dwell time is reached, else None.
        """
        if point is None:
            self.hover_button = None
            self.hover_start = None
            return None

        px, py = point
        target = next((b for b in self.buttons if b.contains(px, py)), None)

        if target is None:
            self.hover_button = None
            self.hover_start = None
            return None

        if self.hover_button is not target:
            self.hover_button = target
            self.hover_start = time.time()
            return None

        if time.time() - self.hover_start >= config.DWELL_TIME_SEC:
            self.hover_button = None
            self.hover_start = None
            return target.action

        return None

    def in_toolbar(self, point):
        return point is not None and point[1] <= self.height