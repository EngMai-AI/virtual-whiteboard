"""
main.py
-------
Entry point for the virtual whiteboard. Wires together the webcam feed,
hand tracking, gesture recognition, drawing canvas, and toolbar.

Run with:  python main.py
Quit with: q   (or close the window)
"""

import time

import cv2

import config
from hand_tracker import HandTracker
from gesture_recognizer import GestureRecognizer
from canvas import Canvas
from toolbar import Toolbar
from utils import PointSmoother


def main():
    cap = cv2.VideoCapture(config.CAM_INDEX)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

    if not cap.isOpened():
        print("ERROR: could not open webcam. Check config.CAM_INDEX or camera permissions.")
        return

    tracker = HandTracker(
        max_hands=config.MAX_HANDS,
        detection_confidence=config.DETECTION_CONFIDENCE,
        tracking_confidence=config.TRACKING_CONFIDENCE,
    )
    recognizer = GestureRecognizer()
    canvas = Canvas(config.CANVAS_WIDTH, config.CANVAS_HEIGHT)
    toolbar = Toolbar(config.CANVAS_WIDTH)
    smoother = PointSmoother(alpha=config.SMOOTHING_FACTOR)

    active_tool = "brush"
    active_color_name = config.DEFAULT_COLOR
    brush_thickness = config.BRUSH_THICKNESS_DEFAULT

    drawing_active = False
    palm_hold_start = None
    prev_time = 0.0

    print("Virtual Whiteboard running. Press 'q' in the window to quit.")

    while True:
        success, frame = cap.read()
        if not success:
            print("Failed to read from webcam.")
            break

        frame = cv2.flip(frame, 1)  # mirror for a natural "looking in a mirror" feel
        frame = cv2.resize(frame, (config.CANVAS_WIDTH, config.CANVAS_HEIGHT))

        frame = tracker.find_hands(frame, draw=True)
        landmarks = tracker.get_landmark_positions(frame)
        handedness = tracker.get_handedness(default="Right")

        gesture = "NONE"
        index_tip = None

        if landmarks:
            fingers = recognizer.fingers_up(landmarks, handedness)
            gesture = recognizer.classify(fingers)
            raw_tip = (landmarks[8][1], landmarks[8][2])
            index_tip = smoother.smooth(raw_tip)
        else:
            smoother.smooth(None)

        # ----- Dispatch gesture -> action -----
        if gesture == "SELECT" and index_tip is not None:
            canvas.end_stroke()
            drawing_active = False
            palm_hold_start = None

            action = toolbar.update_hover(index_tip)
            if action:
                kind, value = action
                if kind == "tool":
                    active_tool = value
                elif kind == "color":
                    active_color_name = value
                elif kind == "thickness":
                    brush_thickness = max(
                        config.BRUSH_THICKNESS_MIN,
                        min(config.BRUSH_THICKNESS_MAX,
                            brush_thickness + value * config.BRUSH_THICKNESS_STEP),
                    )
                elif kind == "history":
                    canvas.undo() if value == "undo" else canvas.redo()
                elif kind == "toggle" and value == "shape_mode":
                    canvas.shape_mode = not canvas.shape_mode
                elif kind == "clear":
                    canvas.clear()
                elif kind == "save":
                    path = canvas.save()
                    print(f"Saved drawing to {path}")

        elif gesture == "DRAW" and index_tip is not None:
            toolbar.update_hover(None)
            palm_hold_start = None

            if toolbar.in_toolbar(index_tip):
                canvas.end_stroke()
                drawing_active = False
            else:
                if not drawing_active:
                    canvas.start_stroke()
                    drawing_active = True
                if active_tool == "eraser":
                    canvas.erase(index_tip, config.ERASER_THICKNESS)
                else:
                    canvas.draw_line(index_tip, config.COLORS[active_color_name], brush_thickness)

        elif gesture == "ERASE" and index_tip is not None:
            toolbar.update_hover(None)
            palm_hold_start = None
            if not drawing_active:
                canvas.start_stroke()
                drawing_active = True
            canvas.erase(index_tip, config.ERASER_THICKNESS)

        elif gesture == "PALM":
            toolbar.update_hover(None)
            canvas.end_stroke()
            drawing_active = False
            if palm_hold_start is None:
                palm_hold_start = time.time()
            elif time.time() - palm_hold_start >= config.CLEAR_HOLD_TIME_SEC:
                canvas.clear()
                palm_hold_start = None

        else:
            toolbar.update_hover(None)
            canvas.end_stroke()
            drawing_active = False
            palm_hold_start = None

        # ----- Compose output -----
        display = canvas.overlay_on(frame)
        toolbar.draw(display, active_tool=active_tool, active_color=active_color_name,
                     shape_mode=canvas.shape_mode)

        status = f"Gesture: {gesture}"
        if gesture == "PALM" and palm_hold_start is not None:
            status += f"  (hold to clear: {time.time() - palm_hold_start:0.1f}s)"
        cv2.putText(display, status, (10, config.CANVAS_HEIGHT - 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        info = (f"Tool: {active_tool}  Color: {active_color_name}  "
                f"Thickness: {brush_thickness}  Shapes: {'ON' if canvas.shape_mode else 'OFF'}")
        cv2.putText(display, info, (10, config.CANVAS_HEIGHT - 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        curr_time = time.time()
        fps = 1 / (curr_time - prev_time) if prev_time else 0
        prev_time = curr_time
        cv2.putText(display, f"FPS: {int(fps)}", (config.CANVAS_WIDTH - 140, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

        cv2.imshow("Virtual Whiteboard", display)

        # ----- Keyboard shortcuts (bonus) -----
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            canvas.clear()
        elif key == ord('s'):
            path = canvas.save()
            print(f"Saved drawing to {path}")
        elif key == ord('z'):
            canvas.undo()
        elif key == ord('y'):
            canvas.redo()
        elif key in (ord('+'), ord('=')):
            brush_thickness = min(config.BRUSH_THICKNESS_MAX, brush_thickness + config.BRUSH_THICKNESS_STEP)
        elif key in (ord('-'), ord('_')):
            brush_thickness = max(config.BRUSH_THICKNESS_MIN, brush_thickness - config.BRUSH_THICKNESS_STEP)
        elif key == ord('b'):
            active_tool = "brush"
        elif key == ord('e'):
            active_tool = "eraser"
        elif key == ord('g'):
            canvas.shape_mode = not canvas.shape_mode
        elif ord('1') <= key <= ord('9'):
            names = list(config.COLORS.keys())
            idx = key - ord('1')
            if idx < len(names):
                active_color_name = names[idx]

    cap.release()
    cv2.destroyAllWindows()
    tracker.close()


if __name__ == "__main__":
    main()
    