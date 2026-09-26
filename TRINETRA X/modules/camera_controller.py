from modules.camera_manager import (
    CameraManager
)

from modules.mode_manager import (
    ModeManager
)


class CameraController:

    def __init__(self, mode="railway"):

        self.camera_manager = (
            CameraManager()
        )

        self.mode_manager = (
            ModeManager(mode)
        )

        self.configure_cameras()

    def configure_cameras(self):

        mode = (
            self.mode_manager.current_mode
        )

        config = (
            self.mode_manager
            .get_configuration()
        )

        print(
            "\n================================"
        )

        print(
            f"CONFIGURING "
            f"{mode.upper()} CAMERAS"
        )

        print(
            "================================"
        )

        # =================================
        # RAILWAY
        # =================================

        if mode == "railway":

            self.camera_manager.add_camera(

                camera_id="CAM001",

                source=0,

                camera_type="zone",

                zone_id="Z001"
            )

            self.camera_manager.add_camera(

                camera_id="CAM002",

                source=1,

                camera_type="train_front",

                zone_id="Z001"
            )

        # =================================
        # ROAD
        # =================================

        elif mode == "road":

            self.camera_manager.add_camera(

                camera_id="CAM003",

                source=2,

                camera_type="zone",

                zone_id="Z002"
            )

            self.camera_manager.add_camera(

                camera_id="CAM004",

                source=3,

                camera_type="vehicle_front",

                zone_id="Z002"
            )

    def switch_mode(self, mode):

        print(
            f"\nSwitching camera system "
            f"to {mode.upper()}..."
        )

        # Release existing cameras

        self.camera_manager.release_all()

        # Create new mode

        self.mode_manager.switch_mode(
            mode
        )

        # Reset manager

        self.camera_manager = (
            CameraManager()
        )

        # Configure new cameras

        self.configure_cameras()

        print(
            f"[CAMERA CONTROLLER] "
            f"{mode.upper()} ACTIVE"
        )

    def get_active_camera_pair(self):

        mode = (
            self.mode_manager.current_mode
        )

        return (
            self.camera_manager
            .get_camera_pair(mode)
        )