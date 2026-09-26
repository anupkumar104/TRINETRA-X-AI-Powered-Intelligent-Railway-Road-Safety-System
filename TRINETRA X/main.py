
import cv2
import time

from database.database import init_db, get_camera_client

from modules.camera_manager import CameraManager
from modules.zone_client_registry import ZoneClientRegistry
from modules.yolo_detector import YOLODetector
from modules.risk_engine import RiskEngine
from modules.critical_event_handler import CriticalEventHandler


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "yolo11n.pt"
CONFIDENCE = 0.40
ALERT_COOLDOWN = 10


# ============================================================
# ANIMAL CLASSES
# ============================================================

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
    "giraffe",
}


# ============================================================
# CAMERA CONFIGURATION
# ============================================================

CAMERAS = {
    "CAM001": {
        "source": 0,
        "camera_type": "zone",
        "zone_id": "Z001",
    },
    "CAM002": {
        "source": 0,
        "camera_type": "train_front",
        "zone_id": "Z001",
    },
    "CAM003": {
        "source": 0,
        "camera_type": "zone",
        "zone_id": "Z002",
    },
    "CAM004": {
        "source": 0,
        "camera_type": "vehicle_front",
        "zone_id": "Z002",
    },
}


# ============================================================
# AI SAFETY SYSTEM
# ============================================================

class AISafetySystem:

    def __init__(self):

        print("\n========================================")
        print("       TRINETRA X")
        print("       AI SAFETY SYSTEM")
        print("========================================")

        print("\n[1] Initializing database...")
        init_db()
        print("[DATABASE] Ready")

        print("\n[2] Initializing Camera Manager...")
        self.camera_manager = CameraManager()

        print("\n[3] Initializing Zone Client Registry...")
        self.client_registry = ZoneClientRegistry()
        print("[CLIENT REGISTRY] Ready")

        print("\n[4] Loading YOLO model...")
        self.detector = YOLODetector(
            model_path=MODEL_PATH,
            confidence=CONFIDENCE,
        )

        if not self.detector.load_model():
            raise RuntimeError("YOLO model could not be loaded.")

        print("\n[5] Initializing Risk Engine...")
        self.risk_engine = RiskEngine()

        print("\n[6] Initializing Critical Event Handler...")
        self.event_handler = CriticalEventHandler()

        self.last_alert_time = {}

        print("\n[SYSTEM READY]")

    # ========================================================
    # REGISTER CAMERAS
    # ========================================================

    def register_cameras(self):

        print("\n========================================")
        print("REGISTERING CAMERAS")
        print("========================================")

        for camera_id, config in CAMERAS.items():

            self.camera_manager.add_camera(
                camera_id=camera_id,
                source=config["source"],
                camera_type=config["camera_type"],
                zone_id=config["zone_id"],
            )

    # ========================================================
    # DISPLAY CAMERAS
    # ========================================================

    def display_cameras(self):

        print("\n========================================")
        print("AVAILABLE CAMERAS")
        print("========================================")

        for camera_id, config in CAMERAS.items():

            print(
                f"{camera_id} | "
                f"{config['camera_type']} | "
                f"Zone {config['zone_id']}"
            )

    # ========================================================
    # GET ACTIVE TARGETS
    # ========================================================

    def display_active_targets(self, zone_id, mode):

        if mode == "railway":

            clients = self.client_registry.get_active_clients(
                zone_id=zone_id,
                client_type="train",
            )

        elif mode == "road":

            clients = self.client_registry.get_active_clients(
                zone_id=zone_id,
                client_type="vehicle",
            )

        else:
            clients = []

        print("\n========== ACTIVE TARGETS ==========")
        print(f"Active targets: {len(clients)}")

        for client in clients:

            print(
                f"  -> {client['client_id']} | "
                f"{client['name']} | "
                f"{client['status']}"
            )

        return clients

    # ========================================================
    # RUN CAMERA
    # ========================================================

    def run_camera(self, camera_id):

        if camera_id not in CAMERAS:
            print(f"[ERROR] Unknown camera: {camera_id}")
            return

        config = CAMERAS[camera_id]

        camera_type = config["camera_type"]
        zone_id = config["zone_id"]
        mode = self._get_mode(zone_id)

        print("\n========================================")
        print(f"PROCESSING CAMERA: {camera_id}")
        print("========================================")
        print(f"[CAMERA] {camera_id}")
        print(f"[TYPE] {camera_type}")
        print(f"[ZONE] {zone_id}")
        print(f"[MODE] {mode}")

        active_targets = self.display_active_targets(
            zone_id=zone_id,
            mode=mode,
        )

        # Open camera only once for this run
        if not self.camera_manager.open_camera(camera_id):
            print("[ERROR] Camera could not open.")
            return

        # Print front-camera assignment only once at startup
        if camera_type in ("train_front", "vehicle_front"):

            assigned_client = get_camera_client(camera_id)

            if assigned_client:

                print(
                    f"[CAMERA ASSIGNMENT] {camera_id} -> "
                    f"{assigned_client['client_id']} | "
                    f"{assigned_client['name']}"
                )

        print("\n[LIVE] Camera started.")
        print("[LIVE] Press Q to stop.")

        frame_count = 0

        try:

            while True:

                # --------------------------------------------
                # READ FRAME
                # --------------------------------------------

                frame = self.camera_manager.read_frame(camera_id)

                if frame is None:
                    print("[ERROR] Could not read frame.")
                    break

                frame_count += 1

                # --------------------------------------------
                # REFRESH ACTIVE TARGETS
                # --------------------------------------------

                if frame_count % 30 == 0:

                    active_targets = self.display_active_targets(
                        zone_id=zone_id,
                        mode=mode,
                    )

                # --------------------------------------------
                # YOLO DETECTION
                # --------------------------------------------

                detections = self.detector.detect(frame)

                # --------------------------------------------
                # FILTER ANIMALS
                # --------------------------------------------

                animal_detections = []

                for detection in detections:

                    class_name = (
                        detection["class_name"]
                        .lower()
                        .strip()
                    )

                    if class_name in ANIMAL_CLASSES:
                        animal_detections.append(detection)

                # --------------------------------------------
                # EVALUATE RISK EVERY FRAME
                # --------------------------------------------

                if camera_type in ("train_front", "vehicle_front"):

                    risk_result = self._front_camera_risk(
                        mode=mode,
                        zone_id=zone_id,
                        camera_id=camera_id,
                        camera_type=camera_type,
                        animal_detections=animal_detections,
                        active_targets=active_targets,
                    )

                elif camera_type == "zone":

                    risk_result = self._zone_camera_risk(
                        mode=mode,
                        zone_id=zone_id,
                        camera_id=camera_id,
                        animal_detections=animal_detections,
                        active_targets=active_targets,
                    )

                else:

                    self.risk_engine.reset(camera_id)

                    risk_result = self._normal_result(
                        "UNKNOWN_CAMERA",
                        "Unknown camera type.",
                    )

                # --------------------------------------------
                # DISPLAY RISK
                # --------------------------------------------

                if animal_detections:

                    print(
                        f"[FRAME {frame_count}] "
                        f"RISK: {risk_result['risk_level']} | "
                        f"SCORE: {risk_result['risk_score']} | "
                        f"DURATION: "
                        f"{risk_result.get('duration', 0)}s"
                    )

                elif frame_count % 30 == 0:

                    print(
                        f"[FRAME {frame_count}] "
                        "No animal detected."
                    )

                # --------------------------------------------
                # CRITICAL EVENT
                # --------------------------------------------

                if (
                    animal_detections
                    and risk_result.get("trigger_critical", False)
                ):

                    self._handle_live_risk(
                        frame=frame,
                        mode=mode,
                        zone_id=zone_id,
                        camera_id=camera_id,
                        animal_detections=animal_detections,
                        risk_result=risk_result,
                    )

                # --------------------------------------------
                # DRAW DETECTIONS
                # --------------------------------------------

                display_frame = frame.copy()

                for animal in animal_detections:

                    x1, y1, x2, y2 = animal["bbox"]

                    label = (
                        f"{animal['class_name']} "
                        f"{animal['confidence']:.2f}"
                    )

                    cv2.rectangle(
                        display_frame,
                        (x1, y1),
                        (x2, y2),
                        (0, 255, 0),
                        2,
                    )

                    cv2.putText(
                        display_frame,
                        label,
                        (x1, max(y1 - 10, 20)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )

                # --------------------------------------------
                # CAMERA INFORMATION OVERLAY
                # --------------------------------------------

                risk_level = risk_result["risk_level"]
                risk_score = risk_result["risk_score"]
                duration = risk_result.get("duration", 0)

                overlay_lines = [
                    (f"Camera: {camera_id}", 30),
                    (f"Zone: {zone_id}", 60),
                    (f"Mode: {mode.upper()}", 90),
                    (f"Active Targets: {len(active_targets)}", 120),
                    (f"Risk: {risk_level} ({risk_score})", 150),
                    (f"Animal Duration: {duration}s", 180),
                ]

                for text, y_position in overlay_lines:

                    color = (
                        (0, 0, 255)
                        if text.startswith("Risk:")
                        and risk_level == "CRITICAL"
                        else (0, 255, 255)
                        if text.startswith("Risk:")
                        else (255, 255, 255)
                    )

                    cv2.putText(
                        display_frame,
                        text,
                        (20, y_position),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        color,
                        2,
                    )

                # --------------------------------------------
                # DISPLAY FRAME
                # --------------------------------------------

                cv2.imshow(
                    "TRINETRA X - AI Safety System",
                    display_frame,
                )

                key = cv2.waitKey(1) & 0xFF

                if key == ord("q"):
                    print("\n[LIVE] Stop requested.")
                    break

        except KeyboardInterrupt:
            print("\n[LIVE] Stopped by user.")

        finally:

            self.camera_manager.release_camera(camera_id)
            cv2.destroyAllWindows()

            print("[LIVE] Camera released.")

    # ========================================================
    # NORMAL RISK RESULT
    # ========================================================

    def _normal_result(self, event_type, reason):

        return {
            "risk_score": 0,
            "risk_level": "NORMAL",
            "event_type": event_type,
            "reason": reason,
            "duration": 0,
            "trigger_critical": False,
        }

    # ========================================================
    # EVALUATE CAMERA-WISE ANIMAL PRESENCE
    # ========================================================

    def _evaluate_camera_presence(
        self,
        camera_id,
        animal_detected,
        event_type,
        reason,
    ):

        result = self.risk_engine.evaluate(
            camera_id=camera_id,
            animal_detected=animal_detected,
        )

        return {
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "event_type": event_type,
            "reason": reason,
            "duration": result["duration"],
            "trigger_critical": result["trigger_critical"],
        }

    # ========================================================
    # FRONT CAMERA RISK
    # ========================================================

    def _front_camera_risk(
        self,
        mode,
        zone_id,
        camera_id,
        camera_type,
        animal_detections,
        active_targets,
    ):

        animal_name = (
            animal_detections[0]["class_name"]
            if animal_detections
            else "Animal"
        )

        assigned_client = get_camera_client(camera_id)

        if assigned_client is None:

            self.risk_engine.reset(camera_id)

            return self._normal_result(
                "NO_CAMERA_ASSIGNMENT",
                (
                    f"{animal_name} detected by {camera_id}, "
                    "but no client is assigned to this camera."
                ),
            )

        if assigned_client["status"] != "ONLINE":

            self.risk_engine.reset(camera_id)

            return self._normal_result(
                "CLIENT_OFFLINE",
                (
                    f"{animal_name} detected by {camera_id}, "
                    f"but assigned client "
                    f"{assigned_client['name']} is "
                    f"{assigned_client['status']}."
                ),
            )

        if assigned_client["zone_id"] != zone_id:

            self.risk_engine.reset(camera_id)

            return self._normal_result(
                "ZONE_MISMATCH",
                (
                    f"{animal_name} detected by {camera_id}, "
                    f"but assigned client "
                    f"{assigned_client['client_id']} "
                    f"is not in Zone {zone_id}."
                ),
            )

        # --------------------------------------------
        # TRAIN FRONT CAMERA
        # --------------------------------------------

        if camera_type == "train_front":

            if assigned_client["client_type"] != "train":

                self.risk_engine.reset(camera_id)

                return self._normal_result(
                    "CLIENT_TYPE_MISMATCH",
                    (
                        f"{camera_id} is a train front camera, "
                        "but its assigned client is not a train."
                    ),
                )

            return self._evaluate_camera_presence(
                camera_id=camera_id,
                animal_detected=bool(animal_detections),
                event_type="ANIMAL_TRAIN_FRONT",
                reason=(
                    f"{animal_name} detected by Train Front "
                    f"Camera {camera_id}, assigned to "
                    f"{assigned_client['name']} "
                    f"in Railway Zone {zone_id}."
                ),
            )

        # --------------------------------------------
        # VEHICLE FRONT CAMERA
        # --------------------------------------------

        if camera_type == "vehicle_front":

            if assigned_client["client_type"] != "vehicle":

                self.risk_engine.reset(camera_id)

                return self._normal_result(
                    "CLIENT_TYPE_MISMATCH",
                    (
                        f"{camera_id} is a vehicle front camera, "
                        "but its assigned client is not a vehicle."
                    ),
                )

            return self._evaluate_camera_presence(
                camera_id=camera_id,
                animal_detected=bool(animal_detections),
                event_type="ANIMAL_VEHICLE_FRONT",
                reason=(
                    f"{animal_name} detected by Vehicle Front "
                    f"Camera {camera_id}, assigned to "
                    f"{assigned_client['name']} "
                    f"in Road Zone {zone_id}."
                ),
            )

        self.risk_engine.reset(camera_id)

        return self._normal_result(
            "UNKNOWN",
            "Unknown front camera.",
        )

    # ========================================================
    # ZONE CAMERA RISK
    # ========================================================

    def _zone_camera_risk(
        self,
        mode,
        zone_id,
        camera_id,
        animal_detections,
        active_targets,
    ):

        animal_name = (
            animal_detections[0]["class_name"]
            if animal_detections
            else "Animal"
        )

        if not active_targets:

            self.risk_engine.reset(camera_id)

            if mode == "railway":

                return self._normal_result(
                    "NO_ACTIVE_TRAIN",
                    (
                        f"{animal_name} detected by Railway Zone "
                        f"Camera {camera_id}, but no active train "
                        f"exists in Railway Zone {zone_id}."
                    ),
                )

            if mode == "road":

                return self._normal_result(
                    "NO_ACTIVE_VEHICLE",
                    (
                        f"{animal_name} detected by Road Zone "
                        f"Camera {camera_id}, but no active "
                        f"vehicle exists in Road Zone {zone_id}."
                    ),
                )

            return self._normal_result(
                "UNKNOWN",
                "Unknown zone mode.",
            )

        if mode == "railway":

            return self._evaluate_camera_presence(
                camera_id=camera_id,
                animal_detected=bool(animal_detections),
                event_type="ANIMAL_TRAIN_SAME_ZONE",
                reason=(
                    f"{animal_name} detected by Railway Zone "
                    f"Camera {camera_id} in Zone {zone_id}."
                ),
            )

        if mode == "road":

            return self._evaluate_camera_presence(
                camera_id=camera_id,
                animal_detected=bool(animal_detections),
                event_type="ANIMAL_VEHICLE_SAME_ZONE",
                reason=(
                    f"{animal_name} detected by Road Zone "
                    f"Camera {camera_id} in Zone {zone_id}."
                ),
            )

        self.risk_engine.reset(camera_id)

        return self._normal_result(
            "UNKNOWN",
            "Unknown zone mode.",
        )

    # ========================================================
    # HANDLE CRITICAL RISK
    # ========================================================

    def _handle_live_risk(
        self,
        frame,
        mode,
        zone_id,
        camera_id,
        animal_detections,
        risk_result,
    ):

        current_time = time.time()
        last_time = self.last_alert_time.get(camera_id, 0)

        if current_time - last_time < ALERT_COOLDOWN:

            print(
                "[ALERT] Cooldown active. "
                "Duplicate alert skipped."
            )

            return

        self.last_alert_time[camera_id] = current_time

        print("\n========================================")
        print("CRITICAL ANIMAL ALERT")
        print("========================================")

        print(f"Camera : {camera_id}")
        print(f"Zone   : {zone_id}")
        print(f"Mode   : {mode.upper()}")
        print(f"Event  : {risk_result['event_type']}")
        print(f"Risk   : {risk_result['risk_level']}")
        print(f"Score  : {risk_result['risk_score']}")
        print(f"Reason : {risk_result['reason']}")

        if not animal_detections:
            print("[ALERT] No current animal detection.")
            return

        best_animal = max(
            animal_detections,
            key=lambda x: x["confidence"],
        )

        result = self.event_handler.handle(
            frame=frame,
            mode=mode,
            zone_id=zone_id,
            camera_id=camera_id,
            animal_detection=best_animal,
            risk_result=risk_result,
        )

        if not result:
            print("[EVENT] Event handler returned no result.")
            return

        print("\n[EVENT COMPLETE]")
        print("Event ID:", result.get("event_id"))
        print("Risk:", result.get("risk_level"))
        print("Event Type:", result.get("event_type"))

    # ========================================================
    # GET MODE
    # ========================================================

    def _get_mode(self, zone_id):

        if zone_id == "Z001":
            return "railway"

        if zone_id == "Z002":
            return "road"

        raise ValueError(f"Unknown zone: {zone_id}")

    # ========================================================
    # CAMERA MENU
    # ========================================================

    def camera_menu(self):

        camera_map = {
            "1": "CAM001",
            "2": "CAM002",
            "3": "CAM003",
            "4": "CAM004",
        }

        while True:

            print("\n========================================")
            print("       TRINETRA X CAMERA MENU")
            print("========================================")
            print("1. CAM001 - Railway Zone")
            print("2. CAM002 - Train Front")
            print("3. CAM003 - Road Zone")
            print("4. CAM004 - Vehicle Front")
            print("5. Exit")
            print("========================================")

            choice = input("Select camera (1-5): ").strip()

            if choice in camera_map:
                self.run_camera(camera_map[choice])

            elif choice == "5":
                print("\n[SYSTEM] Exiting...")
                break

            else:
                print("[ERROR] Invalid choice.")


# ============================================================
# MAIN
# ============================================================

def main():

    system = AISafetySystem()

    system.register_cameras()
    system.display_cameras()
    system.camera_menu()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()