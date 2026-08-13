"""
hand_tracker.py
---------------
Thin wrapper around MediaPipe Hands. Keeps all MediaPipe-specific
plumbing in one place so the rest of the app just deals with plain
(x, y) landmark coordinates.
"""

import cv2
import mediapipe as mp


class HandTracker:
    def __init__(self, max_hands=1, detection_confidence=0.7, tracking_confidence=0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence,
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.mp_styles = mp.solutions.drawing_styles
        self.results = None

    def find_hands(self, frame, draw=True):
        """Run detection on a BGR frame and optionally draw the skeleton overlay."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        self.results = self.hands.process(rgb)

        if draw and self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_lms,
                    self.mp_hands.HAND_CONNECTIONS,
                    self.mp_styles.get_default_hand_landmarks_style(),
                    self.mp_styles.get_default_hand_connections_style(),
                )
        return frame

    def get_landmark_positions(self, frame, hand_index=0):
        """Returns a list of (id, x, y) pixel-space tuples for the requested hand."""
        landmark_list = []
        if self.results and self.results.multi_hand_landmarks:
            if hand_index >= len(self.results.multi_hand_landmarks):
                return landmark_list
            hand = self.results.multi_hand_landmarks[hand_index]
            h, w = frame.shape[:2]
            for idx, lm in enumerate(hand.landmark):
                landmark_list.append((idx, int(lm.x * w), int(lm.y * h)))
        return landmark_list

    def get_handedness(self, hand_index=0, default="Right"):
        """'Left' or 'Right' as reported by MediaPipe, mirrored for the flipped webcam feed."""
        if self.results and self.results.multi_handedness:
            if hand_index < len(self.results.multi_handedness):
                return self.results.multi_handedness[hand_index].classification[0].label
        return default

    def close(self):
        self.hands.close()