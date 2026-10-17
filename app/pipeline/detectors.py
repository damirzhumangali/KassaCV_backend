import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class BoundingBox:
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float
    label: str
    track_id: int | None = None


@dataclass
class DetectionResult:
    frame_idx: int
    timestamp_sec: float
    boxes: list[BoundingBox] = field(default_factory=list)


class ObjectDetector:
    """Detects persons, hands, cash, payment cards, receipts, and registers."""

    def __init__(self, models_dir: Path, device: str = "cpu") -> None:
        self.models_dir = models_dir
        self.device = device
        self.model = None
        self._load_model()

    def _load_model(self) -> None:
        """Attempt to load local YOLO/detector model from models_dir."""
        model_file = next(self.models_dir.glob("*.pt"), None) or next(self.models_dir.glob("*.onnx"), None)
        if model_file:
            try:
                from ultralytics import YOLO
                log.info("Loading object detector from %s on %s", model_file, self.device)
                self.model = YOLO(str(model_file))
                self.model.to(self.device)
            except Exception as e:
                log.warning("Could not initialize detector from %s: %s", model_file, e)
        else:
            log.info("No detector weights found in %s, detector will operate in fallback mode", self.models_dir)

    def detect_batch(self, frames: list[Any], timestamps: list[float]) -> list[DetectionResult]:
        """Perform batch detection over sampled video frames."""
        results: list[DetectionResult] = []

        if self.model is not None and frames and frames[0] is not None:
            try:
                # Batch prediction
                preds = self.model.predict(
                    source=frames,
                    device=self.device,
                    conf=0.25,
                    verbose=False,
                    half=(self.device.startswith("cuda")),
                )
                for idx, (pred, t) in enumerate(zip(preds, timestamps)):
                    boxes: list[BoundingBox] = []
                    for box in pred.boxes:
                        coords = box.xyxy[0].tolist()
                        conf = float(box.conf[0])
                        cls_idx = int(box.cls[0])
                        label = pred.names.get(cls_idx, str(cls_idx))
                        boxes.append(BoundingBox(
                            x1=coords[0],
                            y1=coords[1],
                            x2=coords[2],
                            y2=coords[3],
                            confidence=conf,
                            label=label,
                        ))
                    results.append(DetectionResult(frame_idx=idx, timestamp_sec=t, boxes=boxes))
                return results
            except Exception as exc:
                log.error("Batch detection error: %s, using fallback", exc)

        # Fallback or synthetic detection (e.g. for testing or when weights not yet placed)
        for idx, t in enumerate(timestamps):
            results.append(DetectionResult(frame_idx=idx, timestamp_sec=t, boxes=[]))
        return results
