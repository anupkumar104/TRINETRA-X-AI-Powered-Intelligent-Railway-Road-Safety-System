from modules.mode_manager import ModeManager
from modules.correlation_engine import CorrelationEngine
from modules.risk_engine import RiskEngine
from modules.zone_detector import ZoneDetector


class SafetyPipeline:

    def __init__(self, mode="railway"):

        self.mode_manager = ModeManager(mode)

        self.risk_engine = RiskEngine()

        self.zone_detector = ZoneDetector()

        self.correlation_engine = (
            CorrelationEngine(mode=mode)
        )

        self.configure_zones()

    # ==================================
    # CONFIGURE ZONES
    # ==================================

    def configure_zones(self):

        self.zone_detector = ZoneDetector()

        # Railway Zone
        self.zone_detector.add_zone(
            zone_id="Z001",
            x1=100,
            y1=100,
            x2=800,
            y2=600
        )

        # Road Zone
        self.zone_detector.add_zone(
            zone_id="Z002",
            x1=100,
            y1=100,
            x2=800,
            y2=600
        )

    # ==================================
    # SWITCH MODE
    # ==================================

    def switch_mode(self, mode):

        self.mode_manager.switch_mode(mode)

        self.correlation_engine = (
            CorrelationEngine(mode=mode)
        )

        self.configure_zones()

        print(
            f"[PIPELINE] Mode changed to "
            f"{mode.upper()}"
        )

    # ==================================
    # FILTER OBJECTS IN CURRENT ZONE
    # ==================================

    def filter_zone_objects(
        self,
        detections,
        zone_id
    ):

        result = []

        for detection in detections:

            detected_zone = (
                self.zone_detector
                .get_detection_zone(
                    detection
                )
            )

            if detected_zone == zone_id:

                result.append(detection)

        return result

    # ==================================
    # PROCESS
    # ==================================

    def process(
        self,
        animal_detections,
        target_detections
    ):

        mode = (
            self.mode_manager.current_mode
        )

        zone_id = (
            self.mode_manager.get_zone_id()
        )

        # ------------------------------
        # ONLY CURRENT ZONE OBJECTS
        # ------------------------------

        animals = (
            self.filter_zone_objects(
                animal_detections,
                zone_id
            )
        )

        targets = (
            self.filter_zone_objects(
                target_detections,
                zone_id
            )
        )

        # ------------------------------
        # CORRELATION
        # ------------------------------

        correlation = (
            self.correlation_engine
            .check_correlation(
                zone_id,
                animals,
                targets
            )
        )

        # ------------------------------
        # RISK
        # ------------------------------

        risk = (
            self.risk_engine.calculate_risk(
                mode=mode,
                zone_id=zone_id,
                animal_detections=animals,
                target_detections=targets
            )
        )

        return {

            "mode": mode,

            "zone_id": zone_id,

            "animals_in_zone":
                animals,

            "targets_in_zone":
                targets,

            "correlation":
                correlation,

            "risk":
                risk
        }