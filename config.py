"""
config.py
---------
Central place for every tunable constant used across the app.
Change values here instead of hunting through the codebase.
"""

# ----- Camera / frame settings -----
CAM_INDEX = 0
FRAME_WIDTH = 1280
FRAME_HEIGHT = 720

# ----- Canvas settings (kept equal to frame size so overlay is 1:1) -----
CANVAS_WIDTH = FRAME_WIDTH
CANVAS_HEIGHT = FRAME_HEIGHT

# ----- MediaPipe Hands settings -----
MAX_HANDS = 1
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.7

# ----- Color palette (BGR, since OpenCV uses BGR) -----
COLORS = {
    "Red": (0, 0, 255),
    "Green": (0, 255, 0),
    "Blue": (255, 0, 0),
    "Yellow": (0, 255, 255),
    "White": (255, 255, 255),
    "Purple": (211, 0, 148),
}
DEFAULT_COLOR = "Red"

# ----- Brush / eraser settings -----
BRUSH_THICKNESS_MIN = 2
BRUSH_THICKNESS_MAX = 50
BRUSH_THICKNESS_DEFAULT = 8
BRUSH_THICKNESS_STEP = 2
ERASER_THICKNESS = 40

# ----- Landmark smoothing (0 = no smoothing/jittery, 1 = no movement) -----
SMOOTHING_FACTOR = 0.45

# ----- Toolbar interaction -----
DWELL_TIME_SEC = 1.0          # hover time required to "click" a toolbar button
CLEAR_HOLD_TIME_SEC = 1.5     # open-palm hold time required to clear the canvas

# ----- History -----
MAX_UNDO_STEPS = 20

# ----- Output -----
OUTPUT_DIR = "output"
