class DetectionManager:

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

    TRAIN_CLASSES = {
        "train"
    }

    VEHICLE_CLASSES = {
        "car",
        "motorcycle",
        "bus",
        "truck"
    }

    def __init__(self, mode="railway"):

        self.mode = mode.lower()

    def switch_mode(self, mode):

        mode = mode.lower()

        if mode not in {
            "railway",
            "road"
        }:

            raise ValueError(
                "Mode must be railway or road."
            )

        self.mode = mode

        print(
            f"[DETECTION MANAGER] "
            f"Mode: {mode.upper()}"
        )

    def detect_zone_objects(
        self,
        detections
    ):

        animals = []

        for detection in detections:

            class_name = (
                detection["class_name"]
                .lower()
            )

            if class_name in self.ANIMAL_CLASSES:

                animals.append(
                    detection
                )

        return animals

    def detect_front_objects(
        self,
        detections
    ):

        targets = []

        if self.mode == "railway":

            allowed_classes = (
                self.TRAIN_CLASSES
            )

        else:

            allowed_classes = (
                self.VEHICLE_CLASSES
            )

        for detection in detections:

            class_name = (
                detection["class_name"]
                .lower()
            )

            if class_name in allowed_classes:

                targets.append(
                    detection
                )

        return targets

    def process(
        self,
        zone_detections,
        front_detections
    ):

        animals = (
            self.detect_zone_objects(
                zone_detections
            )
        )

        targets = (
            self.detect_front_objects(
                front_detections
            )
        )

        return {
            "animals": animals,
            "targets": targets,
            "mode": self.mode
        }