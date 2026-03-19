import os
import structlog
import numpy as np
from ultralytics import YOLO

logger = structlog.get_logger()

MODEL_NAME = os.getenv("MODEL_NAME", "yolov10n")
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))

# Classes we care about for security
TARGET_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
    14: "bird",
    15: "cat",
    16: "dog",
}


class Detector:
    def __init__(self):
        model_path = f"/app/models/{MODEL_NAME}.pt"
        if not os.path.exists(model_path):
            logger.info("downloading_model", model=MODEL_NAME)
            self.model = YOLO(f"{MODEL_NAME}.pt")
            self.model.save(model_path)
        else:
            self.model = YOLO(model_path)
        logger.info("model_loaded", model=MODEL_NAME)

    def detect(self, frame: np.ndarray) -> list[dict]:
        results = self.model(frame, conf=CONFIDENCE_THRESHOLD, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue

            for i in range(len(boxes)):
                cls_id = int(boxes.cls[i].item())
                if cls_id not in TARGET_CLASSES:
                    continue

                conf = float(boxes.conf[i].item())
                x1, y1, x2, y2 = boxes.xyxy[i].tolist()

                detections.append({
                    "class_id": cls_id,
                    "label": TARGET_CLASSES[cls_id],
                    "confidence": round(conf, 3),
                    "bbox": {
                        "x1": round(x1),
                        "y1": round(y1),
                        "x2": round(x2),
                        "y2": round(y2),
                    },
                })

        return detections

    def get_event_type(self, label: str) -> str:
        if label == "person":
            return "person"
        if label in ("car", "truck", "bus", "motorcycle", "bicycle"):
            return "vehicle"
        if label in ("cat", "dog", "bird"):
            return "animal"
        return "object"
