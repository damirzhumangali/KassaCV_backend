import logging
from dataclasses import dataclass, field
from typing import Any
from app.pipeline.detectors import BoundingBox, DetectionResult

log = logging.getLogger(__name__)


@dataclass
class TrackedPerson:
    track_id: int
    role: str  # "cashier", "client", "bystander"
    positions: list[tuple[float, float, float]] = field(default_factory=list)  # (timestamp, x_center, y_center)
    zones: list[str] = field(default_factory=list)


@dataclass
class SceneLayout:
    counter_y: float = 0.5  # Relative dividing line or region
    cashier_side: str = "top"  # or "left" / "right" based on camera angle


class SceneTracker:
    """Tracks persons across frames, infers scene layout and assigns roles relatively."""

    def __init__(self) -> None:
        self.next_track_id = 1
        self.active_tracks: dict[int, tuple[float, float]] = {}  # track_id -> last (x, y)

    def track_and_assign_roles(self, detections: list[DetectionResult]) -> list[TrackedPerson]:
        """Track persons across detection results and dynamically assign roles based on relative layout."""
        tracks: dict[int, TrackedPerson] = {}

        # 1. Simple IoU / centroid association across frames
        for frame_det in detections:
            person_boxes = [b for b in frame_det.boxes if b.label.lower() in {"person", "human", "cashier", "customer"}]
            for box in person_boxes:
                cx = (box.x1 + box.x2) / 2.0
                cy = (box.y1 + box.y2) / 2.0

                matched_id = None
                best_dist = float("inf")
                for tid, (lx, ly) in self.active_tracks.items():
                    dist = ((cx - lx) ** 2 + (cy - ly) ** 2) ** 0.5
                    if dist < 150.0 and dist < best_dist:
                        best_dist = dist
                        matched_id = tid

                if matched_id is None:
                    matched_id = self.next_track_id
                    self.next_track_id += 1
                    tracks[matched_id] = TrackedPerson(track_id=matched_id, role="client")

                box.track_id = matched_id
                self.active_tracks[matched_id] = (cx, cy)
                tracks[matched_id].positions.append((frame_det.timestamp_sec, cx, cy))

        # 2. Invariant Relative Role Determination (camera-angle robust)
        # Person with least variance in position near POS counter is identified as cashier
        if len(tracks) >= 2:
            def _stability(person: TrackedPerson) -> float:
                if len(person.positions) < 2:
                    return 0.0
                xs = [p[1] for p in person.positions]
                ys = [p[2] for p in person.positions]
                var_x = sum((x - sum(xs)/len(xs))**2 for x in xs) / len(xs)
                var_y = sum((y - sum(ys)/len(ys))**2 for y in ys) / len(ys)
                return -(var_x + var_y)  # higher is more stationary

            cashier_cand = max(tracks.values(), key=_stability)
            cashier_cand.role = "cashier"
            for t in tracks.values():
                if t.track_id != cashier_cand.track_id:
                    t.role = "client"

        return list(tracks.values())
