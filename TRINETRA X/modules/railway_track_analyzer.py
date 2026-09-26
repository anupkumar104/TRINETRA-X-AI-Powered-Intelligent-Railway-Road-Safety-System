import cv2
import numpy as np


class RailwayTrackAnalyzer:

    def __init__(self):
        self.min_contour_area = 500
        self.max_contour_area = 50000

    def analyze(self, frame):
        """
        Analyze railway track condition.

        Returns:
            {
                "detected": bool,
                "hazard_type": str or None,
                "confidence": float,
                "risk_level": str,
                "reason": str
            }
        """

        if frame is None:
            return self._no_hazard("Invalid frame")

        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Reduce noise
            blur = cv2.GaussianBlur(
                gray,
                (5, 5),
                0
            )

            # Edge detection
            edges = cv2.Canny(
                blur,
                50,
                150
            )

            height, width = edges.shape

            # Focus mainly on lower portion of image
            # where railway track normally appears.
            roi_start = int(height * 0.45)

            roi = edges[
                roi_start:height,
                0:width
            ]

            # Detect straight track-like lines
            lines = cv2.HoughLinesP(
                roi,
                rho=1,
                theta=np.pi / 180,
                threshold=50,
                minLineLength=50,
                maxLineGap=30
            )

            if lines is None:
                return self._no_hazard(
                    "No railway track lines detected"
                )

            left_lines = []
            right_lines = []

            for line in lines:

                # Safely flatten Hough line
                line = np.asarray(line).reshape(-1)

                if len(line) < 4:
                    continue

                x1, y1, x2, y2 = line[:4]

                dx = x2 - x1
                dy = y2 - y1

                if dx == 0:
                    continue

                slope = dy / float(dx)

                # Ignore nearly horizontal lines
                if abs(slope) < 0.3:
                    continue

                if slope < 0:
                    left_lines.append(
                        [x1, y1, x2, y2]
                    )

                else:
                    right_lines.append(
                        [x1, y1, x2, y2]
                    )

            # We need both sides to perform track geometry analysis.
            if not left_lines or not right_lines:
                return self._no_hazard(
                    "Insufficient track geometry"
                )

            left_slope = self._average_slope(
                left_lines
            )

            right_slope = self._average_slope(
                right_lines
            )

            # Normal railway track should have
            # reasonably stable opposite slopes.
            geometry_difference = abs(
                abs(left_slope) -
                abs(right_slope)
            )

            # Current conservative threshold.
            # This is intentionally kept moderate so
            # false alarms can be reduced during testing.
            if geometry_difference > 0.35:

                confidence = min(
                    0.95,
                    0.55 +
                    geometry_difference
                )

                return {
                    "detected": True,
                    "hazard_type":
                        "TRACK_GEOMETRY_ANOMALY",
                    "confidence":
                        round(confidence, 2),
                    "risk_level":
                        "HIGH",
                    "reason":
                        (
                            "Possible abnormal railway "
                            "track geometry detected."
                        )
                }

            return self._no_hazard(
                "Railway track geometry appears normal"
            )

        except Exception as error:

            print(
                f"[TRACK ANALYZER ERROR] {error}"
            )

            return self._no_hazard(
                "Track analysis failed"
            )

    @staticmethod
    def _average_slope(lines):

        slopes = []

        for line in lines:

            # HoughLinesP normally returns:
            # [[x1, y1, x2, y2]]
            # Convert safely to 1D array.

            line = np.asarray(line).reshape(-1)

            if len(line) < 4:
                continue

            x1, y1, x2, y2 = line[:4]

            dx = x2 - x1
            dy = y2 - y1

            if dx == 0:
                continue

            slopes.append(
                dy / float(dx)
            )

        if not slopes:
            return 0.0

        return float(
            np.mean(slopes)
        )

    @staticmethod
    def _no_hazard(reason):

        return {
            "detected": False,
            "hazard_type": None,
            "confidence": 0.0,
            "risk_level": "LOW",
            "reason": reason
        }