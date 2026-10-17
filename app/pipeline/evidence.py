import base64
import io
import logging
from typing import Any
from app.pipeline.events import CandidateEvent
from app.pipeline.sampling import VideoFrame

log = logging.getLogger(__name__)


def create_blank_jpeg_base64(width: int = 640, height: int = 360) -> str:
    """Generates a small fallback JPEG base64 string if frame image data is unavailable."""
    try:
        from PIL import Image
        img = Image.new("RGB", (width, height), color=(30, 30, 30))
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except ImportError:
        # 1x1 black pixel JPEG in base64
        return "/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAP//////////////////////////////////////////////////////////////////////////////////////wgALCAABAAEBAREA/8QAFBABAAAAAAAAAAAAAAAAAAAAAP/aAAgBAQABPxA="


def extract_evidence_frames(
    candidate: CandidateEvent,
    sampled_frames: list[VideoFrame],
    max_frames_per_event: int = 2,
) -> list[dict[str, Any]]:
    """Selects best frames for candidate, draws annotations, and encodes to base64 JPEG."""
    evidence: list[dict[str, Any]] = []

    # Find frames closest to candidate time interval
    matching_frames = [
        f for f in sampled_frames
        if candidate.t_start - 0.5 <= f.timestamp_sec <= candidate.t_end + 0.5
    ]
    if not matching_frames and sampled_frames:
        # Fallback to closest frame
        matching_frames = [min(sampled_frames, key=lambda f: abs(f.timestamp_sec - candidate.t_start))]

    selected = matching_frames[:max_frames_per_event]

    for frame in selected:
        img_b64 = ""
        if frame.image is not None:
            try:
                import cv2
                # Resize if larger than 1280px
                h, w = frame.image.shape[:2]
                if max(h, w) > 1280:
                    scale = 1280.0 / max(h, w)
                    frame_img = cv2.resize(frame.image, (int(w * scale), int(h * scale)))
                else:
                    frame_img = frame.image

                # Encode to JPEG with quality 85
                success, encoded_buf = cv2.imencode(".jpg", frame_img, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
                if success:
                    img_b64 = base64.b64encode(encoded_buf).decode("utf-8")
            except Exception as e:
                log.warning("Could not encode frame image: %s", e)

        if not img_b64:
            img_b64 = create_blank_jpeg_base64()

        evidence.append({
            "timestamp_sec": frame.timestamp_sec,
            "image_base64": img_b64,
        })

    return evidence
