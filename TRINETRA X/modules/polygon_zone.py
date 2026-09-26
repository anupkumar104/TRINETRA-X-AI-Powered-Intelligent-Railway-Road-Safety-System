import cv2
import numpy as np


class PolygonZone:

    def __init__(
        self,
        zone_id,
        points,
        name="Danger Zone"
    ):

        self.zone_id = zone_id

        self.points = np.array(
            points,
            dtype=np.int32
        )

        self.name = name

    # ==================================
    # CHECK POINT
    # ==================================

    def contains_point(self, point):

        x, y = point

        result = cv2.pointPolygonTest(

            self.points,

            (float(x), float(y)),

            False
        )

        return result >= 0

    # ==================================
    # DETECTION CENTER
    # ==================================

    def get_center(self, bbox):

        x1, y1, x2, y2 = bbox

        center_x = int(
            (x1 + x2) / 2
        )

        center_y = int(
            (y1 + y2) / 2
        )

        return center_x, center_y

    # ==================================
    # CHECK DETECTION
    # ==================================

    def is_detection_inside(
        self,
        detection
    ):

        center = self.get_center(
            detection["bbox"]
        )

        return self.contains_point(
            center
        )

    # ==================================
    # DRAW ZONE
    # ==================================

    def draw(
        self,
        frame,
        color=(0, 0, 255),
        thickness=3
    ):

        cv2.polylines(

            frame,

            [
                self.points
            ],

            True,

            color,

            thickness
        )

        # ------------------------------
        # Zone Label
        # ------------------------------

        x, y = self.points[0]

        cv2.putText(

            frame,

            self.name,

            (int(x), int(y) - 10),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            color,

            2
        )

        return frame

    # ==================================
    # DRAW DETECTION STATUS
    # ==================================

    def draw_detection_status(
        self,
        frame,
        detection
    ):

        center = self.get_center(
            detection["bbox"]
        )

        inside = (
            self.contains_point(
                center
            )
        )

        if inside:

            status = "INSIDE ZONE"

            color = (0, 0, 255)

        else:

            status = "OUTSIDE ZONE"

            color = (0, 255, 0)

        x1, y1, x2, y2 = (
            detection["bbox"]
        )

        # Bounding box

        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            color,

            2
        )

        # Center point

        cv2.circle(

            frame,

            center,

            5,

            color,

            -1
        )

        # Status

        cv2.putText(

            frame,

            status,

            (x1, y1 - 10),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.6,

            color,

            2
        )

        return inside