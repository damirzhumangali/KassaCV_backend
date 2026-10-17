import logging
import tempfile
import time
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.pipeline.aggregate import aggregate_and_format_verdict
from app.pipeline.detectors import ObjectDetector
from app.pipeline.events import TemporalRuleEngine
from app.pipeline.ingest import normalize_video, probe_video
from app.pipeline.sampling import sample_frames
from app.pipeline.tracking import SceneTracker
from app.pipeline.vlm import VLMVerifier
from app.rules.catalog import load_catalog

log = logging.getLogger(__name__)

# Cache models across worker calls to prevent reloading per job
_DETECTOR: ObjectDetector | None = None
_CATALOG: dict[str, dict[str, Any]] | None = None


def get_detector() -> ObjectDetector:
    global _DETECTOR
    if _DETECTOR is None:
        settings = get_settings()
        _DETECTOR = ObjectDetector(models_dir=settings.models_dir, device=settings.device)
    return _DETECTOR


def get_rules_catalog() -> dict[str, dict[str, Any]]:
    global _CATALOG
    if _CATALOG is None:
        settings = get_settings()
        _CATALOG = load_catalog(settings.rules_path)
    return _CATALOG


def analyze_video(video_path: str, deadline_epoch: float) -> dict[str, Any]:
    """
    Orchestrates the 8 pipeline stages with strict deadline budget enforcement.
    Budget guide (total 60-140s, max 240s):
    1. Ingest & normalize
    2. Sampling (2-5 fps)
    3. Detection
    4. Tracking & relative zones
    5. Temporal rules
    6. VLM candidate verification
    7. Aggregation & evidence extraction
    """
    settings = get_settings()
    src_path = Path(video_path)

    if not src_path.exists() or src_path.stat().st_size == 0:
        raise ValueError("Video file does not exist or is empty")

    catalog = get_rules_catalog()
    t_start = time.time()
    log.info("Starting pipeline execution for job on video: %s (deadline in %.1fs)", src_path.name, deadline_epoch - t_start)

    # Stage 1: Ingest & Probe
    meta = probe_video(src_path)
    log.info("Stage 1 (Ingest): duration=%.1fs, dims=%dx%d, fps=%.1f [elapsed: %.2fs]",
             meta.duration_sec, meta.width, meta.height, meta.fps, time.time() - t_start)

    # Stage 2: Normalization (if needed)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=True) as tmp_norm:
        norm_path = Path(tmp_norm.name)
        active_video_path = normalize_video(src_path, norm_path, max_dimension=1280, target_fps=settings.frame_sample_fps)

        if time.time() >= deadline_epoch - 15.0:
            log.warning("Deadline imminent after ingest/normalization, concluding early")
            return {"verdict": "no_violation", "violations": []}

        # Stage 3: Sampling
        t_sample_start = time.time()
        sampled_frames = sample_frames(active_video_path, target_fps=settings.frame_sample_fps)
        log.info("Stage 2 (Sampling): %d frames extracted [elapsed: %.2fs]", len(sampled_frames), time.time() - t_sample_start)

        if not sampled_frames:
            # Fallback if video couldn't produce frames
            return {"verdict": "no_violation", "violations": []}

        # Stage 4: Detection
        t_detect_start = time.time()
        detector = get_detector()
        timestamps = [f.timestamp_sec for f in sampled_frames]
        images = [f.image for f in sampled_frames]

        detections = detector.detect_batch(images, timestamps)
        log.info("Stage 3 (Detection): processed %d frames [elapsed: %.2fs]", len(detections), time.time() - t_detect_start)

        # Stage 5: Tracking, relative roles and zones
        t_track_start = time.time()
        tracker = SceneTracker()
        tracks = tracker.track_and_assign_roles(detections)
        log.info("Stage 4 (Tracking): tracked %d persons [elapsed: %.2fs]", len(tracks), time.time() - t_track_start)

        # Stage 6: Temporal rules state machines
        t_rules_start = time.time()
        rule_engine = TemporalRuleEngine(catalog=catalog)
        candidates = rule_engine.evaluate_candidates(detections, tracks)
        log.info("Stage 5 (Rules): identified %d violation candidates [elapsed: %.2fs]", len(candidates), time.time() - t_rules_start)

        # Stage 7 & 8: VLM verification & Aggregation
        vlm_verifier = VLMVerifier(catalog=catalog, device=settings.device)
        result = aggregate_and_format_verdict(
            candidates=candidates,
            sampled_frames=sampled_frames,
            catalog=catalog,
            vlm_verifier=vlm_verifier,
            confidence_threshold=0.5,
        )

    log.info("Pipeline completed in %.2fs. Verdict: %s, Violations count: %d",
             time.time() - t_start, result.get("verdict"), len(result.get("violations", [])))
    return result
