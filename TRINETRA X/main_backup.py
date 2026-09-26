import cv2
import time

from database.database import init_db

from modules.camera_manager import CameraManager
from modules.yolo_detector import YOLODetector
from modules.risk_engine import RiskEngine
from modules.critical_event_handler import CriticalEventHandler
from modules.zone_client_registry import ZoneClientRegistry


# ==========================================
# CONFIGURATION
# ==========================================

MODEL_PATH = "yolo11n.pt"
CONFIDENCE = 0.40

# Camera to test
TEST_CAMERA = "CAM001"

# Duplicate alert prevention
ALERT_COOLDOWN = 10


# ==========================================
# ANIMAL CLASSES
# ==========================================

ANIMAL_CLASSES = {
    "bird",
    "cat",
    "dog",
    "horse",
    "sheep",
    "cow",
    "elephant",
    "bear",
    "zebra",
    "giraffe"
}


# ==========================================
# AI SAFETY SYSTEM
# ==========================================

class AISafetySystem:

    def __init__(self):

        print("\n========================================")
        print("       AI SAFETY SYSTEM")
        print("       LIVE PIPELINE")
        print("========================================")

        # ==================================
        # DATABASE
        # ==================================

        print("\n[1] Initializing database...")

        init_db()

        print("[DATABASE] Ready")

        # ==================================
        # CAMERA MANAGER
        # ==================================

        print("\n[2] Initializing Camera Manager...")

        self.camera_manager = CameraManager()

        # ==================================
        # CLIENT REGISTRY
        # ==================================

        print("\n[3] Initializing Zone Client Registry...")

        self.client_registry = ZoneClientRegistry()

        print("[CLIENT REGISTRY] Ready")

        # ==================================
        # YOLO
        # ==================================

        print("\n[4] Loading YOLO model...")

        self.detector = YOLODetector(
            model_path=MODEL_PATH,
            confidence=CONFIDENCE
        )

        if not self.detector.load_model():

            raise RuntimeError(
                "YOLO model could not be loaded."
            )

        # ==================================
        # RISK ENGINE
        # ==================================

        self.risk_engine = RiskEngine()

        # ==================================
        # EVENT HANDLER
        # ==================================

        self.event_handler = CriticalEventHandler()

        # ==================================
        # ALERT CONTROL
        # ==================================

        self.last_alert_time = {}

        print("\n[SYSTEM READY]")


    # ======================================
    # ADD CAMERA
    # ======================================

    def add_camera(
        self,
        camera_id,
        source,
        camera_type,
        zone_id
    ):

        self.camera_manager.add_camera(

            camera_id=camera_id,

            source=source,

            camera_type=camera_type,

            zone_id=zone_id
        )


    # ======================================
    # GET MODE
    # ======================================

    def _get_mode(
        self,
        zone_id
    ):

        if zone_id == "Z001":

            return "railway"

        if zone_id == "Z002":

            return "road"

        raise ValueError(
            f"Unknown zone: {zone_id}"
        )


    # ======================================
    # GET ACTIVE TARGETS
    # ======================================

    def _get_active_targets(
        self,
        mode,
        zone_id
    ):

        # ==================================
        # RAILWAY
        # ==================================

        if mode == "railway":

            trains = (
                self.client_registry
                .get_active_clients(
                    zone_id=zone_id,
                    client_type="train"
                )
            )

            return trains

        # ==================================
        # ROAD
        # ==================================

        if mode == "road":

            vehicles = (
                self.client_registry
                .get_active_clients(
                    zone_id=zone_id,
                    client_type="vehicle"
                )
            )

            return vehicles

        return []


    # ======================================
    # DISPLAY ACTIVE TARGETS
    # ======================================

    def _display_active_targets(
        self,
        mode,
        zone_id
    ):

        targets = self._get_active_targets(
            mode,
            zone_id
        )

        print("\n========== ACTIVE TARGETS ==========")

        if not targets:

            print(
                f"No active {mode} targets "
                f"in zone {zone_id}."
            )

            return targets

        print(
            f"Active {mode} targets: "
            f"{len(targets)}"
        )

        for target in targets:

            print(
                f"  → "
                f"{target['client_id']} | "
                f"{target['name']} | "
                f"{target['status']}"
            )

        return targets


    # ======================================
    # PROCESS LIVE CAMERA
    # ======================================

    def run_live_camera(
        self,
        camera_id
    ):

        camera_info = (
            self.camera_manager.get_camera_info(
                camera_id
            )
        )

        if camera_info is None:

            print(
                f"[ERROR] Camera "
                f"{camera_id} not found."
            )

            return

        mode = self._get_mode(
            camera_info["zone_id"]
        )

        zone_id = camera_info["zone_id"]

        camera_type = camera_info["camera_type"]

        print("\n========================================")
        print(
            f"PROCESSING LIVE CAMERA: {camera_id}"
        )
        print("========================================")

        print(
            f"[CAMERA] {camera_id}"
        )

        print(
            f"[TYPE] {camera_type}"
        )

        print(
            f"[ZONE] {zone_id}"
        )

        print(
            f"[MODE] {mode}"
        )

        # ==================================
        # SHOW ACTIVE TARGETS
        # ==================================

        if camera_type == "zone":

            self._display_active_targets(
                mode,
                zone_id
            )

        # ==================================
        # OPEN CAMERA
        # ==================================

        if not self.camera_manager.open_camera(
            camera_id
        ):

            print(
                "[ERROR] Camera could not open."
            )

            return

        print(
            "\n[LIVE] Camera started."
        )

        print(
            "[LIVE] Press Q to stop."
        )

        frame_count = 0

        try:

            while True:

                # ==================================
                # READ FRAME
                # ==================================

                frame = (
                    self.camera_manager.read_frame(
                        camera_id
                    )
                )

                if frame is None:

                    print(
                        "[ERROR] Could not read frame."
                    )

                    break

                frame_count += 1

                # ==================================
                # YOLO DETECTION
                # ==================================

                detections = (
                    self.detector.detect(
                        frame
                    )
                )

                # ==================================
                # ANIMAL FILTER
                # ==================================

                animal_detections = []

                for detection in detections:

                    class_name = (
                        detection["class_name"]
                        .lower()
                        .strip()
                    )

                    if class_name in ANIMAL_CLASSES:

                        animal_detections.append(
                            detection
                        )

                # ==================================
                # STATUS
                # ==================================

                if animal_detections:

                    print(
                        f"\n[FRAME {frame_count}] "
                        f"ANIMAL DETECTED"
                    )

                    for animal in animal_detections:

                        print(
                            f"  → "
                            f"{animal['class_name']} "
                            f"({animal['confidence']:.2f})"
                        )

                    # ==================================
                    # FRONT CAMERA
                    # ==================================

                    if camera_type in (
                        "train_front",
                        "vehicle_front"
                    ):

                        risk_result = (
                            self._front_camera_risk(

                                mode=mode,

                                zone_id=zone_id,

                                camera_id=camera_id,

                                camera_type=camera_type,

                                animal_detections=(
                                    animal_detections
                                )
                            )
                        )

                    # ==================================
                    # ZONE CAMERA
                    # ==================================

                    elif camera_type == "zone":

                        risk_result = (
                            self._zone_camera_risk(

                                mode=mode,

                                zone_id=zone_id,

                                camera_id=camera_id,

                                animal_detections=(
                                    animal_detections
                                )
                            )
                        )

                    else:

                        risk_result = {

                            "risk_score": 0,

                            "risk_level": "NORMAL",

                            "event_type":
                                "UNKNOWN",

                            "reason":
                                "Unknown camera type."
                        }

                    # ==================================
                    # DISPLAY RISK
                    # ==================================

                    print(
                        f"[RISK] "
                        f"{risk_result['risk_level']} "
                        f"| Score: "
                        f"{risk_result['risk_score']}"
                    )

                    # ==================================
                    # CRITICAL EVENT
                    # ==================================

                    if (
                        risk_result["risk_level"]
                        == "CRITICAL"
                    ):

                        self._handle_live_risk(

                            frame=frame,

                            mode=mode,

                            zone_id=zone_id,

                            camera_id=camera_id,

                            animal_detections=(
                                animal_detections
                            ),

                            risk_result=risk_result
                        )

                else:

                    if frame_count % 30 == 0:

                        print(
                            f"[FRAME {frame_count}] "
                            f"No animal detected."
                        )

                # ==================================
                # DISPLAY CAMERA
                # ==================================

                display_frame = frame.copy()

                # ==================================
                # DRAW ANIMAL BOXES
                # ==================================

                for animal in animal_detections:

                    x1, y1, x2, y2 = (
                        animal["bbox"]
                    )

                    label = (
                        f"{animal['class_name']} "
                        f"{animal['confidence']:.2f}"
                    )

                    cv2.rectangle(

                        display_frame,

                        (x1, y1),

                        (x2, y2),

                        (0, 255, 0),

                        2
                    )

                    cv2.putText(

                        display_frame,

                        label,

                        (
                            x1,
                            max(
                                y1 - 10,
                                20
                            )
                        ),

                        cv2.FONT_HERSHEY_SIMPLEX,

                        0.6,

                        (0, 255, 0),

                        2
                    )

                # ==================================
                # CAMERA INFORMATION
                # ==================================

                cv2.putText(

                    display_frame,

                    f"Camera: {camera_id}",

                    (20, 30),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255, 255, 255),

                    2
                )

                cv2.putText(

                    display_frame,

                    f"Zone: {zone_id}",

                    (20, 60),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255, 255, 255),

                    2
                )

                cv2.putText(

                    display_frame,

                    f"Mode: {mode.upper()}",

                    (20, 90),

                    cv2.FONT_HERSHEY_SIMPLEX,

                    0.7,

                    (255, 255, 255),

                    2
                )

                cv2.imshow(

                    "AI Safety System",

                    display_frame
                )

                # ==================================
                # STOP WITH Q
                # ==================================

                key = (
                    cv2.waitKey(1)
                    & 0xFF
                )

                if key == ord("q"):

                    print(
                        "\n[LIVE] Stop requested."
                    )

                    break

        except KeyboardInterrupt:

            print(
                "\n[LIVE] Stopped by user."
            )

        finally:

            self.camera_manager.release_camera(
                camera_id
            )

            cv2.destroyAllWindows()

            print(
                "[LIVE] Camera released."
            )


    # ======================================
    # HANDLE LIVE RISK
    # ======================================

    def _handle_live_risk(
        self,
        frame,
        mode,
        zone_id,
        camera_id,
        animal_detections,
        risk_result
    ):

        # ==================================
        # COOLDOWN
        # ==================================

        current_time = time.time()

        last_time = self.last_alert_time.get(
            camera_id,
            0
        )

        if (
            current_time - last_time
            < ALERT_COOLDOWN
        ):

            print(
                "[ALERT] Cooldown active. "
                "Duplicate alert skipped."
            )

            return

        # ==================================
        # UPDATE ALERT TIME
        # ==================================

        self.last_alert_time[
            camera_id
        ] = current_time

        # ==================================
        # CRITICAL ALERT
        # ==================================

        print(
            "\n========================================"
        )

        print(
            "🚨 CRITICAL ANIMAL ALERT"
        )

        print(
            "========================================"
        )

        print(
            f"Camera : {camera_id}"
        )

        print(
            f"Zone   : {zone_id}"
        )

        print(
            f"Mode   : {mode.upper()}"
        )

        print(
            f"Event  : "
            f"{risk_result['event_type']}"
        )

        # ==================================
        # BEST ANIMAL
        # ==================================

        best_animal = max(

            animal_detections,

            key=lambda x:
                x["confidence"]
        )

        # ==================================
        # EVENT HANDLER
        # ==================================

        result = (
            self.event_handler.handle(

                frame=frame,

                mode=mode,

                zone_id=zone_id,

                camera_id=camera_id,

                animal_detection=(
                    best_animal
                ),

                risk_result=risk_result
            )
        )

        print(
            "\n[EVENT COMPLETE]"
        )

        print(
            "Event ID:",
            result["event_id"]
        )

        print(
            "Risk:",
            result["risk_level"]
        )

        print(
            "Event Type:",
            result["event_type"]
        )


    # ======================================
    # FRONT CAMERA RISK
    # ======================================

    def _front_camera_risk(
        self,
        mode,
        zone_id,
        camera_id,
        camera_type,
        animal_detections
    ):

        animal = max(

            animal_detections,

            key=lambda x:
                x["confidence"]
        )

        animal_name = (
            animal["class_name"]
        )

        # ==================================
        # TRAIN FRONT
        # ==================================

        if camera_type == "train_front":

            return {

                "risk_score": 80,

                "risk_level":
                    "CRITICAL",

                "event_type":
                    "ANIMAL_TRAIN_FRONT",

                "reason":
                    (
                        f"{animal_name} detected "
                        f"by Train Front Camera "
                        f"{camera_id} assigned to "
                        f"Train T001 in Railway "
                        f"Zone {zone_id}."
                    )
            }

        # ==================================
        # VEHICLE FRONT
        # ==================================

        if camera_type == "vehicle_front":

            return {

                "risk_score": 90,

                "risk_level":
                    "CRITICAL",

                "event_type":
                    "ANIMAL_VEHICLE_FRONT",

                "reason":
                    (
                        f"{animal_name} detected "
                        f"by Vehicle Front Camera "
                        f"{camera_id} assigned to "
                        f"Vehicle V001 in Road "
                        f"Zone {zone_id}."
                    )
            }

        return {

            "risk_score": 0,

            "risk_level":
                "NORMAL",

            "event_type":
                "UNKNOWN",

            "reason":
                "Unknown front camera."
        }


    # ======================================
    # ZONE CAMERA RISK
    # ======================================

    def _zone_camera_risk(
        self,
        mode,
        zone_id,
        camera_id,
        animal_detections
    ):

        # ==================================
        # CHECK ACTIVE TARGETS
        # ==================================

        active_targets = (
            self._get_active_targets(
                mode=mode,
                zone_id=zone_id
            )
        )

        # ==================================
        # NO ACTIVE TARGET
        # ==================================

        if not active_targets:

            animal = max(

                animal_detections,

                key=lambda x:
                    x["confidence"]
            )

            animal_name = (
                animal["class_name"]
            )

            print(
                f"[ZONE SAFETY] "
                f"Animal detected, but "
                f"no active {mode} target "
                f"in {zone_id}."
            )

            return {

                "risk_score": 0,

                "risk_level":
                    "NORMAL",

                "event_type":
                    "NO_ACTIVE_TARGET",

                "reason":
                    (
                        f"{animal_name} detected "
                        f"by Zone Camera "
                        f"{camera_id}, but no "
                        f"active {mode} target "
                        f"exists in Zone {zone_id}."
                    )
            }

        # ==================================
        # ANIMAL + ACTIVE TARGET
        # ==================================

        animal = max(

            animal_detections,

            key=lambda x:
                x["confidence"]
        )

        animal_name = (
            animal["class_name"]
        )

        # ==================================
        # RAILWAY
        # ==================================

        if mode == "railway":

            target_names = ", ".join(
                target["client_id"]
                for target in active_targets
            )

            return {

                "risk_score": 90,

                "risk_level":
                    "CRITICAL",

                "event_type":
                    "ANIMAL_TRAIN_SAME_ZONE",

                "reason":
                    (
                        f"{animal_name} detected "
                        f"by Railway Zone Camera "
                        f"{camera_id} in Railway "
                        f"Zone {zone_id} while "
                        f"train movement is ACTIVE. "
                        f"Active trains: "
                        f"{target_names}."
                    )
            }

        # ==================================
        # ROAD
        # ==================================

        if mode == "road":

            target_names = ", ".join(
                target["client_id"]
                for target in active_targets
            )

            return {

                "risk_score": 90,

                "risk_level":
                    "CRITICAL",

                "event_type":
                    "ANIMAL_VEHICLE_SAME_ZONE",

                "reason":
                    (
                        f"{animal_name} detected "
                        f"by Road Zone Camera "
                        f"{camera_id} in Road "
                        f"Zone {zone_id} while "
                        f"vehicle movement is ACTIVE. "
                        f"Active vehicles: "
                        f"{target_names}."
                    )
            }

        return {

            "risk_score": 0,

            "risk_level":
                "NORMAL",

            "event_type":
                "UNKNOWN",

            "reason":
                "Unknown zone mode."
        }


# ==========================================
# MAIN
# ==========================================

def main():

    system = AISafetySystem()

    # ======================================
    # CAMERA CONFIGURATION
    # ======================================

    system.add_camera(

        camera_id="CAM001",

        source=0,

        camera_type="zone",

        zone_id="Z001"
    )

    system.add_camera(

        camera_id="CAM002",

        source=0,

        camera_type="train_front",

        zone_id="Z001"
    )

    system.add_camera(

        camera_id="CAM003",

        source=0,

        camera_type="zone",

        zone_id="Z002"
    )

    system.add_camera(

        camera_id="CAM004",

        source=0,

        camera_type="vehicle_front",

        zone_id="Z002"
    )

    # ======================================
    # DISPLAY CAMERAS
    # ======================================

    print(
        "\n========================================"
    )

    print(
        "AVAILABLE CAMERAS"
    )

    print(
        "========================================"
    )

    for camera_id in (
        "CAM001",
        "CAM002",
        "CAM003",
        "CAM004"
    ):

        info = (
            system.camera_manager
            .get_camera_info(
                camera_id
            )
        )

        print(
            f"{camera_id} | "
            f"{info['camera_type']} | "
            f"Zone {info['zone_id']}"
        )

    # ======================================
    # START LIVE CAMERA
    # ======================================

    print(
        "\n========================================"
    )

    print(
        "LIVE CAMERA TEST"
    )

    print(
        "========================================"
    )

    print(
        f"Starting {TEST_CAMERA}..."
    )

    print(
        "Press Q in the camera window to stop."
    )

    system.run_live_camera(
        TEST_CAMERA
    )


# ==========================================
# ENTRY POINT
# ==========================================

if __name__ == "__main__":

    main()