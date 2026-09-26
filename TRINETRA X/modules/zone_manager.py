import cv2


class ZoneManager:

    def __init__(self, zones=None):

        if zones is None:
            zones = {}

        self.zones = zones

    def add_rectangle_zone(
        self,
        zone_id,
        x1,
        y1,
        x2,
        y2
    ):
        """
        Add a rectangular danger zone.
        """

        self.zones[zone_id] = {
            "type": "rectangle",
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2
        }

    def is_point_inside(
        self,
        zone_id,
        point
    ):
        """
        Check whether a point is inside a zone.
        """

        if zone_id not in self.zones:
            return False

        zone = self.zones[zone_id]

        if zone["type"] != "rectangle":
            return False

        px, py = point

        return (
            zone["x1"] <= px <= zone["x2"]
            and
            zone["y1"] <= py <= zone["y2"]
        )

    def is_detection_inside(
        self,
        zone_id,
        bbox
    ):
        """
        Check whether the center of
        a detection bounding box is
        inside the specified zone.
        """

        x1, y1, x2, y2 = bbox

        center_x = int(
            (x1 + x2) / 2
        )

        center_y = int(
            (y1 + y2) / 2
        )

        inside = self.is_point_inside(
            zone_id,
            (center_x, center_y)
        )

        return inside, (
            center_x,
            center_y
        )

    def draw_zone(
        self,
        frame,
        zone_id,
        color=(0, 0, 255),
        thickness=2
    ):
        """
        Draw zone on the frame.
        """

        if zone_id not in self.zones:
            return frame

        zone = self.zones[zone_id]

        if zone["type"] != "rectangle":
            return frame

        cv2.rectangle(
            frame,
            (
                zone["x1"],
                zone["y1"]
            ),
            (
                zone["x2"],
                zone["y2"]
            ),
            color,
            thickness
        )

        cv2.putText(
            frame,
            f"DANGER ZONE: {zone_id}",
            (
                zone["x1"],
                max(
                    zone["y1"] - 10,
                    20
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2
        )

        return frame