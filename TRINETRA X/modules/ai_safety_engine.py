from modules.mode_manager import ModeManager
from modules.detection_manager import DetectionManager
from modules.safety_pipeline import SafetyPipeline
from modules.critical_event_handler import CriticalEventHandler


class AISafetyEngine:

    def __init__(self, mode="railway"):

        print(
            "\n================================"
        )

        print(
            "AI SAFETY ENGINE"
        )

        print(
            "================================"
        )

        # -------------------------------
        # Mode
        # -------------------------------

        self.mode_manager = ModeManager(
            mode
        )

        # -------------------------------
        # Detection
        # -------------------------------

        self.detection_manager = (
            DetectionManager(mode)
        )

        # -------------------------------
        # Safety Pipeline
        # -------------------------------

        self.safety_pipeline = (
            SafetyPipeline(mode)
        )

        # -------------------------------
        # Critical Event Handler
        # -------------------------------

        self.event_handler = (
            CriticalEventHandler()
        )

        print(
            "[ENGINE] Initialized successfully."
        )

    # ===================================
    # MODE SWITCH
    # ===================================

    def switch_mode(self, mode):

        mode = mode.lower().strip()

        print(
            f"\n[ENGINE] Switching to "
            f"{mode.upper()}"
        )

        self.mode_manager.switch_mode(
            mode
        )

        self.detection_manager.switch_mode(
            mode
        )

        self.safety_pipeline.switch_mode(
            mode
        )

        print(
            f"[ENGINE] "
            f"{mode.upper()} MODE ACTIVE"
        )

    # ===================================
    # PROCESS FRAME DETECTIONS
    # ===================================

    def process_detections(
        self,
        zone_detections,
        front_detections,
        frame=None,
        camera_id=None
    ):

        mode = (
            self.mode_manager.current_mode
        )

        zone_id = (
            self.mode_manager.get_zone_id()
        )

        print(
            "\n================================"
        )

        print(
            "PROCESSING SAFETY EVENT"
        )

        print(
            "================================"
        )

        print(
            f"Mode: {mode.upper()}"
        )

        print(
            f"Zone: {zone_id}"
        )

        # --------------------------------
        # Detection Manager
        # --------------------------------

        detections = (
            self.detection_manager.process(
                zone_detections,
                front_detections
            )
        )

        animals = detections[
            "animals"
        ]

        targets = detections[
            "targets"
        ]

        print(
            f"Animals detected: "
            f"{len(animals)}"
        )

        print(
            f"Targets detected: "
            f"{len(targets)}"
        )

        # --------------------------------
        # Safety Pipeline
        # --------------------------------

        result = (
            self.safety_pipeline.process(
                animal_detections=animals,
                target_detections=targets
            )
        )

        risk = result["risk"]

        correlation = (
            result["correlation"]
        )

        print(
            f"Same Zone: "
            f"{correlation['same_zone']}"
        )

        print(
            f"Risk: "
            f"{risk['risk_level']}"
        )

        print(
            f"Risk Score: "
            f"{risk['risk_score']}"
        )

        # --------------------------------
        # CRITICAL EVENT
        # --------------------------------

        if (
            risk["risk_level"]
            == "CRITICAL"
            and frame is not None
            and len(animals) > 0
        ):

            print(
                "\n🚨 CRITICAL EVENT DETECTED"
            )

            event_result = (
                self.event_handler.handle(

                    frame=frame,

                    mode=mode,

                    zone_id=zone_id,

                    camera_id=camera_id,

                    animal_detection=(
                        animals[0]
                    ),

                    risk_result=risk
                )
            )

            return {
                "status": "CRITICAL",
                "risk": risk,
                "correlation": correlation,
                "event": event_result
            }

        # --------------------------------
        # CRITICAL WITHOUT FRAME
        # --------------------------------

        if (
            risk["risk_level"]
            == "CRITICAL"
        ):

            print(
                "\n🚨 CRITICAL DETECTED"
            )

            print(
                "Snapshot/event handler "
                "waiting for camera frame."
            )

            return {
                "status": "CRITICAL",
                "risk": risk,
                "correlation": correlation,
                "event": None
            }

        # --------------------------------
        # NORMAL / MEDIUM
        # --------------------------------

        return {
            "status": risk[
                "risk_level"
            ],

            "risk": risk,

            "correlation": correlation,

            "event": None
        }