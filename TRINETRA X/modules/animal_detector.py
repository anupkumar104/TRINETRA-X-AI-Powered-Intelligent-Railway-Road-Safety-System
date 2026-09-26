from modules.detector import ObjectDetector


# Animals supported by the default YOLO COCO model
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


class AnimalDetector:

    def __init__(self):

        self.detector = ObjectDetector()

    def detect_animals(self, frame):

        detections = (
            self.detector.get_detections(frame)
        )

        animal_detections = []

        for detection in detections:

            object_name = (
                detection["class_name"]
                .lower()
            )

            if object_name in ANIMAL_CLASSES:

                animal_detections.append(
                    detection
                )

        return animal_detections