from ultralytics import YOLO

from config import CONFIDENCE_THRESHOLD


class ObjectDetector:

    def __init__(self, model_name="yolo11n.pt"):

        print(
            f"Loading YOLO model: {model_name}"
        )

        self.model = YOLO(model_name)

        print(
            "YOLO model loaded successfully."
        )

    def detect(self, frame):

        results = self.model(
            frame,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False
        )

        return results

    def get_detections(self, frame):

        results = self.detect(frame)

        detections = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                x1, y1, x2, y2 = (
                    box.xyxy[0].tolist()
                )

                confidence = float(
                    box.conf[0]
                )

                class_id = int(
                    box.cls[0]
                )

                class_name = (
                    self.model.names[class_id]
                )

                detections.append({

                    "class_id": class_id,

                    "class_name": class_name,

                    "confidence": confidence,

                    "bbox": [
                        int(x1),
                        int(y1),
                        int(x2),
                        int(y2)
                    ]
                })

        return detections