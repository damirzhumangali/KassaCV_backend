import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class VideoFrame:
    index: int
    timestamp_sec: float
    image: Any  # numpy.ndarray (BGR/RGB) or None


def sample_frames(video_path: Path, target_fps: float = 3.0, max_frames: int = 600) -> list[VideoFrame]:
    """Sample frames from video at target_fps (2-5 fps)."""
    frames: list[VideoFrame] = []
    try:
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            log.warning("Could not open video %s for frame sampling", video_path)
            return frames

        orig_fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        step = max(1, int(round(orig_fps / target_fps)))

        current_idx = 0
        sampled_count = 0
        while cap.isOpened() and sampled_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            if current_idx % step == 0:
                timestamp_sec = round(current_idx / orig_fps, 2)
                frames.append(VideoFrame(
                    index=current_idx,
                    timestamp_sec=timestamp_sec,
                    image=frame,
                ))
                sampled_count += 1
            current_idx += 1

        cap.release()
        log.info("Sampled %d frames from %s (source fps: %.2f, step: %d)", len(frames), video_path.name, orig_fps, step)
    except ImportError:
        log.warning("cv2 not available; returning dummy frame sequence for testing")
        # Lightweight dummy frames for non-cv2 environments
        for i in range(10):
            frames.append(VideoFrame(index=i, timestamp_sec=float(i), image=None))

    return frames
