class ModeManager:

    MODES = {
        "railway": {
            "zone_id": "Z001",
            "zone_camera": "CAM001",
            "front_camera": "CAM002",
            "front_type": "train_front",
            "target": "train"
        },

        "road": {
            "zone_id": "Z002",
            "zone_camera": "CAM003",
            "front_camera": "CAM004",
            "front_type": "vehicle_front",
            "target": "vehicle"
        }
    }

    def __init__(self, mode="railway"):

        self.current_mode = None

        self.switch_mode(mode)

    def switch_mode(self, mode):

        mode = mode.lower().strip()

        if mode not in self.MODES:

            raise ValueError(
                f"Invalid mode: {mode}. "
                f"Use railway or road."
            )

        self.current_mode = mode

        print(
            f"\nMode switched to: "
            f"{mode.upper()}"
        )

        self.show_configuration()

    def get_configuration(self):

        return self.MODES[
            self.current_mode
        ]

    def get_zone_id(self):

        return self.get_configuration()[
            "zone_id"
        ]

    def get_zone_camera(self):

        return self.get_configuration()[
            "zone_camera"
        ]

    def get_front_camera(self):

        return self.get_configuration()[
            "front_camera"
        ]

    def get_target(self):

        return self.get_configuration()[
            "target"
        ]

    def show_configuration(self):

        config = self.get_configuration()

        print(
            "--------------------------------"
        )

        print(
            f"Mode          : "
            f"{self.current_mode.upper()}"
        )

        print(
            f"Zone          : "
            f"{config['zone_id']}"
        )

        print(
            f"Zone Camera   : "
            f"{config['zone_camera']}"
        )

        print(
            f"Front Camera  : "
            f"{config['front_camera']}"
        )

        print(
            f"Front Type    : "
            f"{config['front_type']}"
        )

        print(
            f"Target        : "
            f"{config['target']}"
        )

        print(
            "--------------------------------"
        )