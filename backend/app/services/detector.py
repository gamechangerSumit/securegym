from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Detection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    track_id: str | None = None


class Detector(Protocol):
    def detect(self, frame) -> list[Detection]:
        """Return detections for a BGR frame."""


class NoopDetector:
    """Safe default until a gym-validated equipment model is configured."""

    def detect(self, frame) -> list[Detection]:
        return []


class UltralyticsDetector:
    """Optional YOLO adapter; configured weights must be trained/validated for gym equipment."""

    def __init__(self, model_path: str, confidence: float = 0.45):
        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise RuntimeError("Install SecureGym with the vision extra to use YOLO") from exc
        self.model = YOLO(model_path)
        self.confidence = confidence

    def detect(self, frame) -> list[Detection]:
        results = self.model.track(
            frame, persist=True, conf=self.confidence, verbose=False, tracker="bytetrack.yaml"
        )
        detections: list[Detection] = []
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                class_id = int(box.cls[0].item())
                label = str(self.model.names[class_id])
                confidence = float(box.conf[0].item())
                coords = tuple(float(v) for v in box.xyxy[0].tolist())
                track_id = str(int(box.id[0].item())) if box.id is not None else None
                detections.append(Detection(label, confidence, coords, track_id))
        return detections
