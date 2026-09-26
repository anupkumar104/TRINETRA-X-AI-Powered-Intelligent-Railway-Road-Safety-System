from pathlib import Path


class YOLODetector:

    def __init__(
        self,
        model_path=None,
        confidence=0.40
    ):
        self.model_path = model_path
        self.confidence = confidence
        self.model = None

    # ==================================
    # LOAD MODEL
    # ==================================

    def load_model(self):

        if self.model_path is None:

            print(
                "[YOLO] No model path provided."
            )

            return False

        model_path = Path(
            self.model_path
        )

        if not model_path.exists():

            print(
                f"[YOLO] Model not found: "
                f"{model_path}"
            )

            return False

        try:

            from ultralytics import YOLO

            self.model = YOLO(
                str(model_path)
            )

            print(
                f"[YOLO] Model loaded successfully: "
                f"{model_path}"
            )

            return True

        except ImportError:

            print(
                "[YOLO] ultralytics is not installed."
            )

            print(
                "Run: pip install ultralytics"
            )

            return False

        except Exception as e:

            print(
                f"[YOLO] Model loading failed: {e}"
            )

            return False

    # ==================================
    # DETECT
    # ==================================

    def detect(self, frame):

        if self.model is None:

            raise RuntimeError(
                "YOLO model is not loaded."
            )

        results = self.model.predict(

            source=frame,

            conf=self.confidence,

            verbose=False
        )

        detections = []

        for result in results:

            if result.boxes is None:

                continue

            boxes = result.boxes

            for i in range(len(boxes)):

                class_id = int(
                    boxes.cls[i].item()
                )

                confidence = float(
                    boxes.conf[i].item()
                )

                x1, y1, x2, y2 = (
                    boxes.xyxy[i].tolist()
                )

                class_name = (
                    result.names[class_id]
                )

                detections.append({

                    "class_name":
                        class_name,

                    "confidence":
                        round(
                            confidence,
                            4
                        ),

                    "bbox": [
                        int(x1),
                        int(y1),
                        int(x2),
                        int(y2)
                    ]
                })

        return detections