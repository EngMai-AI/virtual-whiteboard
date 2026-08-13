"""
gesture_recognizer.py
----------------------
Turns raw hand landmarks into a small, well-defined vocabulary of
gestures the rest of the app can react to.

Supported gestures:
    DRAW   - only the index finger is up            -> draw/erase with the fingertip
    SELECT - index + middle fingers up ("peace")     -> move over the toolbar to pick tools
    ERASE  - closed fist (no fingers up)             -> free erase while moving
    PALM   - all five fingers up (open palm)         -> hold to clear the canvas
    IDLE   - anything else                           -> no action
"""

# Landmark indices for fingertips, per MediaPipe's hand model
TIP_IDS = [4, 8, 12, 16, 20]


class GestureRecognizer:
    def fingers_up(self, landmark_list, handedness="Right"):
        """
        Returns a list of 5 booleans: [thumb, index, middle, ring, pinky]
        True = finger extended.
        """
        if not landmark_list or len(landmark_list) < 21:
            return [False] * 5

        lm = {idx: (x, y) for idx, x, y in landmark_list}
        fingers = []

        # Thumb: compare tip x to the joint below it. Direction flips with handedness
        # because the webcam feed is mirrored before processing.
        if handedness == "Right":
            fingers.append(lm[4][0] > lm[3][0])
        else:
            fingers.append(lm[4][0] < lm[3][0])

        # Other four fingers: tip is "up" if it's above (smaller y than) its PIP joint.
        for tip_id in TIP_IDS[1:]:
            pip_id = tip_id - 2
            fingers.append(lm[tip_id][1] < lm[pip_id][1])

        return fingers

    def classify(self, fingers):
        """fingers: [thumb, index, middle, ring, pinky] -> gesture name string."""
        if not fingers:
            return "IDLE"

        thumb, index, middle, ring, pinky = fingers
        count = sum(fingers)

        if index and not middle and not ring and not pinky:
            return "DRAW"
        if index and middle and not ring and not pinky:
            return "SELECT"
        if count == 0:
            return "ERASE"
        if count == 5:
            return "PALM"
        return "IDLE"