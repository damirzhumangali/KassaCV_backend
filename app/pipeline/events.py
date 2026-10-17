import logging
from dataclasses import dataclass, field
from typing import Any
from app.pipeline.detectors import DetectionResult
from app.pipeline.tracking import TrackedPerson

log = logging.getLogger(__name__)


@dataclass
class CandidateEvent:
    rule_id: str
    rule_type: str
    t_start: float
    t_end: float
    score: float
    key_frame_indices: list[int] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)


class TemporalRuleEngine:
    """State-machine evaluation over temporal sequences of detections and tracked entities."""

    def __init__(self, catalog: dict[str, dict[str, Any]]) -> None:
        self.catalog = catalog

    def evaluate_candidates(
        self,
        detections: list[DetectionResult],
        tracks: list[TrackedPerson],
    ) -> list[CandidateEvent]:
        """Runs temporal rules to find violation candidates."""
        candidates: list[CandidateEvent] = []

        if not detections:
            return candidates

        # Rule R-02: Unauthorized person in restricted cashier zone
        # Detect client track intruding into cashier region
        cashier_track = next((t for t in tracks if t.role == "cashier"), None)
        if cashier_track and len(cashier_track.positions) > 0:
            avg_cashier_x = sum(p[1] for p in cashier_track.positions) / len(cashier_track.positions)
            avg_cashier_y = sum(p[2] for p in cashier_track.positions) / len(cashier_track.positions)

            for client in tracks:
                if client.role != "client":
                    continue
                intruding_frames = []
                for (t_sec, cx, cy) in client.positions:
                    dist = ((cx - avg_cashier_x) ** 2 + (cy - avg_cashier_y) ** 2) ** 0.5
                    if dist < 60.0:  # extremely close / behind the counter
                        intruding_frames.append(t_sec)

                if len(intruding_frames) >= 3:  # prolonged presence (> 1 second)
                    t_start = min(intruding_frames)
                    t_end = max(intruding_frames)
                    rule_info = self.catalog.get("R-02", {})
                    candidates.append(CandidateEvent(
                        rule_id="R-02",
                        rule_type=rule_info.get("type", "Нахождение постороннего лица в служебной кассовой зоне"),
                        t_start=t_start,
                        t_end=t_end,
                        score=0.85,
                        key_frame_indices=[0],
                        context={"details": "Посторонний находился в служебной зоне кассы рядом с кассиром"}
                    ))

        # Additional rules can be registered here based on dataset annotations
        return candidates
