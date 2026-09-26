from modules.polygon_zone import (
    PolygonZone
)


class ZoneDetector:

    def __init__(self):

        self.zones = {}

    # ==================================
    # ADD POLYGON ZONE
    # ==================================

    def add_polygon_zone(
        self,
        zone_id,
        points,
        name="Danger Zone"
    ):

        self.zones[zone_id] = (
            PolygonZone(

                zone_id=zone_id,

                points=points,

                name=name
            )
        )

        print(
            f"[POLYGON ZONE ADDED] "
            f"{zone_id}"
        )

    # ==================================
    # GET ZONE
    # ==================================

    def get_zone(
        self,
        zone_id
    ):

        return self.zones.get(
            zone_id
        )

    # ==================================
    # GET DETECTION ZONE
    # ==================================

    def get_detection_zone(
        self,
        detection
    ):

        for zone_id, zone in (
            self.zones.items()
        ):

            if zone.is_detection_inside(
                detection
            ):

                return zone_id

        return None

    # ==================================
    # SAME ZONE
    # ==================================

    def same_zone(
        self,
        detection_1,
        detection_2
    ):

        zone_1 = (
            self.get_detection_zone(
                detection_1
            )
        )

        zone_2 = (
            self.get_detection_zone(
                detection_2
            )
        )

        return (

            zone_1 is not None

            and

            zone_1 == zone_2
        )

    # ==================================
    # DRAW ZONE
    # ==================================

    def draw_zones(
        self,
        frame
    ):

        for zone in (
            self.zones.values()
        ):

            zone.draw(frame)

        return frame

    # ==================================
    # DRAW OBJECTS
    # ==================================

    def draw_detection(
        self,
        frame,
        detection
    ):

        zone_id = (
            self.get_detection_zone(
                detection
            )
        )

        for current_id, zone in (
            self.zones.items()
        ):

            zone.draw_detection_status(
                frame,
                detection
            )

        return zone_id