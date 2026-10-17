import asyncio
import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.auth import require_api_key
from app.config import get_settings
from app.db import JobStore
from app.schemas import JobAccepted
from app.storage import new_job_id

router = APIRouter(dependencies=[Depends(require_api_key)])
ALLOWED_SUFFIXES = {".mov", ".mp4", ".m4v", ".avi", ".mkv", ".webm", ".mpeg", ".mpg"}


async def _save_limited(upload: UploadFile, dest: Path, limit: int) -> int:
    total = 0
    try:
        with dest.open("xb") as out:
            while chunk := await upload.read(1024 * 1024):
                total += len(chunk)
                if total > limit:
                    raise HTTPException(413, "Upload exceeds configured size limit")
                out.write(chunk)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
    return total


@router.post("/analyze", response_model=JobAccepted, status_code=202)
async def submit_video(request: Request, file: UploadFile = File(...)) -> JobAccepted:
    settings = get_settings()
    if Path(file.filename or "").suffix.lower() not in ALLOWED_SUFFIXES:
        raise HTTPException(415, "Unsupported video extension")
    store: JobStore = request.app.state.store
    if store.queue_size() >= settings.max_queue_size:
        raise HTTPException(429, "Job queue is full")
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    job_id = new_job_id()
    fd, temp_name = tempfile.mkstemp(prefix=f"{job_id}_", suffix=Path(file.filename or "video").suffix.lower(), dir=settings.upload_dir)
    os.close(fd)
    path = Path(temp_name)
    try:
        size = await _save_limited(file, path, settings.max_upload_mb * 1024 * 1024)
        if size == 0:
            raise HTTPException(400, "Uploaded file is empty")
        store.create(job_id, path)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()
    return JobAccepted(job_id=job_id)
