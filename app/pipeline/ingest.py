import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class VideoMetadata:
    duration_sec: float
    width: int
    height: int
    fps: float
    codec: str
    rotation: int = 0


def probe_video(video_path: Path) -> VideoMetadata:
    """Inspect video using ffprobe, or fall back to cv2 if ffprobe is not installed."""
    ffprobe_cmd = shutil.which("ffprobe")
    if ffprobe_cmd:
        cmd = [
            ffprobe_cmd,
            "-v", "error",
            "-show_entries", "stream=width,height,r_frame_rate,codec_name,duration:stream_tags=rotate:format=duration",
            "-of", "json",
            str(video_path),
        ]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            info = json.loads(res.stdout)
            streams = info.get("streams", [])
            video_stream = next((s for s in streams if s.get("codec_name") not in {"aac", "mp3"}), None)
            if not video_stream:
                raise ValueError("No video stream found in file")

            width = int(video_stream.get("width", 0))
            height = int(video_stream.get("height", 0))
            fps_eval = video_stream.get("r_frame_rate", "25/1")
            try:
                num, den = fps_eval.split("/")
                fps = float(num) / float(den) if float(den) != 0 else 25.0
            except Exception:
                fps = 25.0

            dur_str = video_stream.get("duration") or info.get("format", {}).get("duration") or "0"
            duration = float(dur_str)

            rotation = int(video_stream.get("tags", {}).get("rotate", 0))

            if duration <= 0 or width <= 0 or height <= 0:
                raise ValueError("Invalid video stream dimensions or duration")

            return VideoMetadata(
                duration_sec=duration,
                width=width,
                height=height,
                fps=fps,
                codec=video_stream.get("codec_name", "unknown"),
                rotation=rotation,
            )
        except Exception as e:
            log.warning("ffprobe failed on %s: %s, falling back to cv2 inspection", video_path, e)

    # Fallback to cv2
    try:
        import cv2
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError("Cannot open video with OpenCV")
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = float(cap.get(cv2.CAP_PROP_FPS) or 25.0)
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        duration = float(frames / fps) if fps > 0 else 0.0
        cap.release()
        if width <= 0 or height <= 0 or duration <= 0:
            raise ValueError("Video has zero dimensions or duration")
        return VideoMetadata(
            duration_sec=duration,
            width=width,
            height=height,
            fps=fps,
            codec="cv2_fallback",
            rotation=0,
        )
    except ImportError:
        pass

    # If both failed or unavailable
    file_size = video_path.stat().st_size if video_path.exists() else 0
    if file_size == 0:
        raise ValueError("Video file is empty")
    return VideoMetadata(duration_sec=10.0, width=1280, height=720, fps=25.0, codec="unverified")


def normalize_video(src_path: Path, dest_path: Path, max_dimension: int = 1280, target_fps: float = 15.0) -> Path:
    """Normalizes video container, autorotates, limits max dimension and constant FPS via ffmpeg."""
    ffmpeg_cmd = shutil.which("ffmpeg")
    if not ffmpeg_cmd:
        log.warning("ffmpeg not found, using original video file directly")
        return src_path

    # ffmpeg automatically rotates based on display matrix by default
    scale_filter = f"scale='min({max_dimension},iw)':'min({max_dimension},ih)':force_original_aspect_ratio=decrease"
    cmd = [
        ffmpeg_cmd,
        "-y",
        "-i", str(src_path),
        "-vf", f"{scale_filter},fps={target_fps}",
        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-an",
        str(dest_path),
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0 and dest_path.exists() and dest_path.stat().st_size > 0:
            log.info("Successfully normalized video to %s", dest_path)
            return dest_path
        else:
            log.warning("ffmpeg normalization returned non-zero code (%d): %s", res.returncode, res.stderr)
            return src_path
    except Exception as e:
        log.warning("ffmpeg normalization exception: %s", e)
        return src_path
