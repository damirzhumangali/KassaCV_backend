import pytest
from app.pipeline.detectors import BoundingBox, DetectionResult
from app.pipeline.events import TemporalRuleEngine
from app.pipeline.tracking import SceneTracker, TrackedPerson
from app.pipeline.aggregate import aggregate_and_format_verdict
from app.pipeline.vlm import VLMVerifier


def test_scene_tracker_roles():
    tracker = SceneTracker()
    # Person 1 stationary near counter (cashier), Person 2 moving (client)
    det1 = DetectionResult(frame_idx=0, timestamp_sec=0.0, boxes=[
        BoundingBox(x1=100, y1=100, x2=150, y2=200, confidence=0.9, label="person"),
        BoundingBox(x1=300, y1=300, x2=350, y2=400, confidence=0.9, label="person"),
    ])
    det2 = DetectionResult(frame_idx=1, timestamp_sec=1.0, boxes=[
        BoundingBox(x1=102, y1=101, x2=152, y2=201, confidence=0.9, label="person"),
        BoundingBox(x1=350, y1=350, x2=400, y2=450, confidence=0.9, label="person"),
    ])
    tracks = tracker.track_and_assign_roles([det1, det2])
    assert len(tracks) == 2
    roles = {t.role for t in tracks}
    assert "cashier" in roles
    assert "client" in roles


def test_aggregate_empty_violations():
    catalog = {"R-01": {"type": "Test", "interpretation": "Test", "source": "Source", "clause": "Clause"}}
    vlm = VLMVerifier(catalog=catalog)
    res = aggregate_and_format_verdict(candidates=[], sampled_frames=[], catalog=catalog, vlm_verifier=vlm)
    assert res["verdict"] == "no_violation"
    assert res["violations"] == []
