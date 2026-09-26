class CorrelationEngine:

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

    def check_correlation(
        self,
        zone_id,
        zone_detections,
        front_detections
    ):
        """
        Check whether an animal and train/vehicle
        are detected in the same configured zone.
        """

        animals = []

        for detection in zone_detections:

            name = (
                detection["class_name"]
                .lower()
            )

            if name in self.ANIMAL_CLASSES:

                animals.append(detection)

        if self.mode == "railway":

            targets = []

            for detection in front_detections:

                name = (
                    detection["class_name"]
                    .lower()
                )

                if name in self.TRAIN_CLASSES:

                    targets.append(detection)

        elif self.mode == "road":

            targets = []

            for detection in front_detections:

                name = (
                    detection["class_name"]
                    .lower()
                )

                if name in self.VEHICLE_CLASSES:

                    targets.append(detection)

        else:

            targets = []

        animal_present = len(animals) > 0

        target_present = len(targets) > 0

        same_zone = (
            animal_present
            and target_present
        )

        if same_zone:

            if self.mode == "railway":

                event_type = (
                    "ANIMAL_TRAIN_SAME_ZONE"
                )

                message = (
                    f"Animal and train detected "
                    f"in zone {zone_id}"
                )

            else:

                event_type = (
                    "ANIMAL_VEHICLE_SAME_ZONE"
                )

                message = (
                    f"Animal and vehicle detected "
                    f"in zone {zone_id}"
                )

            return {
                "risk": "CRITICAL",
                "same_zone": True,
                "event_type": event_type,
                "message": message,
                "animals": animals,
                "targets": targets
            }

        return {
            "risk": "NORMAL",
            "same_zone": False,
            "event_type": None,
            "message": "No same-zone danger detected.",
            "animals": animals,
            "targets": targets
        }