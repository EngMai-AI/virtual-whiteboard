"""
utils.py
--------
Small standalone helpers shared across modules.
"""


class PointSmoother:
    """
    Exponential moving average smoother for fingertip coordinates.
    Raw MediaPipe landmarks jitter a few pixels frame to frame, which
    shows up as a shaky line; smoothing removes most of that without
    adding noticeable lag.
    """

    def __init__(self, alpha=0.5):
        self.alpha = alpha  # higher = more responsive, lower = smoother
        self.prev = None

    def smooth(self, point):
        if point is None:
            self.prev = None
            return None
        if self.prev is None:
            self.prev = point
            return point
        x = int(self.alpha * point[0] + (1 - self.alpha) * self.prev[0])
        y = int(self.alpha * point[1] + (1 - self.alpha) * self.prev[1])
        self.prev = (x, y)
        return (x, y)