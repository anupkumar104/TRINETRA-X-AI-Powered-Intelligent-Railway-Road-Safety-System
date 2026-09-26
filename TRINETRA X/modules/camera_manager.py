
import cv2
import os


class CameraManager:

    def __init__(self):
        self.cameras = {}

    # ==================================
    # ADD CAMERA
    # ==================================

    def add_camera(
        self,
        camera_id,
        source,
        camera_type,
        zone_id
    ):
        self.cameras[camera_id] = {
            "source": source,
            "camera_type": camera_type,
            "zone_id": zone_id,
            "capture": None
        }

        print(f"[CAMERA ADDED] {camera_id}")

    # ==================================
    # OPEN CAMERA OR VIDEO FILE
    # ==================================

    def open_camera(self, camera_id):

        if camera_id not in self.cameras:
            print(f"[ERROR] Camera {camera_id} not found.")
            return False

        camera = self.cameras[camera_id]

        # Reuse existing open capture
        existing_capture = camera.get("capture")

        if existing_capture is not None:
            if existing_capture.isOpened():
                return True

            existing_capture.release()
            camera["capture"] = None

        source = camera["source"]

        # Validate local video path
        if isinstance(source, str):
            if not os.path.isfile(source):
                print(f"[ERROR] Video file not found: {source}")
                return False

        # Works with webcam index, video path, or stream URL
        capture = cv2.VideoCapture(source)

        if not capture.isOpened():
            print(f"[ERROR] Could not open {camera_id}")
            capture.release()
            return False

        camera["capture"] = capture

        print(f"[CAMERA OPENED] {camera_id}")
        print(f"[SOURCE] {source}")

        return True

    # ==================================
    # CHANGE CAMERA SOURCE
    # ==================================

    def set_camera_source(self, camera_id, source):

        if camera_id not in self.cameras:
            print(f"[ERROR] Camera {camera_id} not found.")
            return False

        # Validate local file before changing source
        if isinstance(source, str):
            if not os.path.isfile(source):
                print(f"[ERROR] Video file not found: {source}")
                return False

        camera = self.cameras[camera_id]

        # Release previous capture
        capture = camera.get("capture")

        if capture is not None:
            capture.release()
            camera["capture"] = None

        camera["source"] = source

        print(
            f"[CAMERA SOURCE UPDATED] "
            f"{camera_id} -> {source}"
        )

        return True

    # ==================================
    # READ FRAME
    # ==================================

    def read_frame(self, camera_id):

        if camera_id not in self.cameras:
            return None

        capture = self.cameras[camera_id]["capture"]

        if capture is None:
            return None

        success, frame = capture.read()

        if not success:
            return None

        return frame

    # ==================================
    # RELEASE CAMERA
    # ==================================

    def release_camera(self, camera_id):

        if camera_id not in self.cameras:
            return

        capture = self.cameras[camera_id].get("capture")

        if capture is not None:
            capture.release()
            self.cameras[camera_id]["capture"] = None

            print(f"[CAMERA RELEASED] {camera_id}")

    # ==================================
    # RELEASE ALL CAMERAS
    # ==================================

    def release_all(self):

        for camera_id in self.cameras:
            self.release_camera(camera_id)

    # ==================================
    # CAMERA INFORMATION
    # ==================================

    def get_camera_info(self, camera_id):

        if camera_id not in self.cameras:
            return None

        camera = self.cameras[camera_id]

        return {
            "camera_id": camera_id,
            "camera_type": camera["camera_type"],
            "zone_id": camera["zone_id"],
            "source": camera["source"]
        }

    # ==================================
    # ACTIVE CAMERAS BY MODE
    # ==================================

    def get_active_cameras(self, mode):

        mode = mode.lower().strip()

        if mode == "railway":
            return ["CAM001", "CAM002"]

        elif mode == "road":
            return ["CAM003", "CAM004"]

        raise ValueError(f"Invalid mode: {mode}")

    # ==================================
    # CAMERA PAIR BY MODE
    # ==================================

    def get_camera_pair(self, mode):

        mode = mode.lower().strip()

        if mode == "railway":
            return {
                "zone_camera": "CAM001",
                "front_camera": "CAM002"
            }

        elif mode == "road":
            return {
                "zone_camera": "CAM003",
                "front_camera": "CAM004"
            }

        raise ValueError(f"Invalid mode: {mode}")

    # ==================================
    # FRONT CAMERA CLIENT
    # ==================================

    def get_front_camera_client(self, camera_id):

        camera_client_map = {
            "CAM002": "T001",
            "CAM004": "V001"
        }

        return camera_client_map.get(camera_id)

    # ==================================
    # CAMERA ROUTING INFORMATION
    # ==================================

    def get_routing_info(self, camera_id):

        camera = self.get_camera_info(camera_id)

        if camera is None:
            return None

        camera_type = camera["camera_type"]
        zone_id = camera["zone_id"]

        # Front cameras: individual routing
        if camera_type in ["train_front", "vehicle_front"]:

            client_id = self.get_front_camera_client(camera_id)

            return {
                "camera_id": camera_id,
                "camera_type": camera_type,
                "zone_id": zone_id,
                "routing": "INDIVIDUAL",
                "client_id": client_id
            }

        # Zone cameras: broadcast routing
        if camera_type == "zone":

            return {
                "camera_id": camera_id,
                "camera_type": camera_type,
                "zone_id": zone_id,
                "routing": "ZONE_BROADCAST",
                "client_id": None
            }

        return {
            "camera_id": camera_id,
            "camera_type": camera_type,
            "zone_id": zone_id,
            "routing": "UNKNOWN",
            "client_id": None
        }