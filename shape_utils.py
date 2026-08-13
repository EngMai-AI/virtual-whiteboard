"""
shape_utils.py
--------------
Bonus feature: automatic geometric shape correction.

Given the raw list of points from a freehand stroke, tries to recognise
whether the user intended a straight line, a rectangle, or a circle/ellipse,
and returns a description of the "cleaned up" shape to render instead of
the wobbly freehand version.
"""

import cv2
import numpy as np


def correct_shape(points, color, thickness):
    """
    points: list of (x, y) pixel tuples captured during one stroke.
    Returns a dict describing the corrected shape, or None if the
    stroke is too short / ambiguous to correct.
    """
    if len(points) < 6:
        return None

    pts = np.array(points, dtype=np.int32)
    stroke_len = cv2.arcLength(pts.reshape(-1, 1, 2), False)
    if stroke_len < 1e-3:
        return None

    start, end = pts[0], pts[-1]
    closed = np.linalg.norm(start.astype(float) - end.astype(float)) < 0.15 * stroke_len

    if not closed:
        # Open stroke -> treat as a straight line between its endpoints.
        return {"type": "line", "p1": tuple(int(v) for v in start),
                "p2": tuple(int(v) for v in end), "color": color, "thickness": thickness}

    hull = cv2.convexHull(pts)
    peri = cv2.arcLength(hull, True)
    area = cv2.contourArea(hull)
    if peri <= 0:
        return None

    circularity = 4 * np.pi * area / (peri * peri)
    # Looser epsilon = fewer vertices in the approximation, so a wobbly
    # hand-drawn rectangle still collapses to ~4 points instead of 6-8.
    approx = cv2.approxPolyDP(hull, 0.04 * peri, True)

    # A hand-drawn circle from a single fingertip is never perfectly round
    # (tracking jitter, frame-to-frame sampling). 0.75 was tuned for a
    # geometrically perfect circle and almost never fires on real input;
    # 0.68 plus an aspect-ratio check on the bounding box (a lopsided oval
    # traced quickly) still reliably rejects rectangles/lines while
    # accepting real circular strokes.
    (cx, cy), radius = cv2.minEnclosingCircle(pts)
    x, y, w, h = cv2.boundingRect(hull)
    aspect_ratio = w / h if h else 0
    is_round_ish = 0.7 < aspect_ratio < 1.3

    if circularity > 0.68 and is_round_ish:
        return {"type": "circle", "center": (int(cx), int(cy)), "radius": int(radius),
                "color": color, "thickness": thickness}

    if len(approx) == 4:
        return {"type": "rectangle", "p1": (x, y), "p2": (x + w, y + h),
                "color": color, "thickness": thickness}

    return {"type": "polygon", "points": [tuple(int(v) for v in p[0]) for p in approx],
            "color": color, "thickness": thickness}


def render_shape(canvas_img, shape):
    """Draws a shape dict (as produced by correct_shape) onto a numpy image."""
    if shape is None:
        return
    color = shape["color"]
    thickness = shape["thickness"]

    if shape["type"] == "line":
        cv2.line(canvas_img, shape["p1"], shape["p2"], color, thickness, cv2.LINE_AA)
    elif shape["type"] == "circle":
        cv2.circle(canvas_img, shape["center"], shape["radius"], color, thickness, cv2.LINE_AA)
    elif shape["type"] == "rectangle":
        cv2.rectangle(canvas_img, shape["p1"], shape["p2"], color, thickness)
    elif shape["type"] == "polygon":
        pts = np.array(shape["points"], dtype=np.int32)
        cv2.polylines(canvas_img, [pts], isClosed=True, color=color, thickness=thickness, lineType=cv2.LINE_AA)