import logging
import threading
import time
from pathlib import Path

from app.config import get_settings
from app.db import JobStore
from app.pipeline.runner import analyze_video
from app.storage import remove_file

log = logging.getLogger(__name__)


def worker_loop(store: JobStore, stop: threading.Event) -> None:
    settings = get_settings()
    while not stop.is_set():
        job = store.claim()
        if job is None:
            stop.wait(0.5)
            continue
        video_path = job["video_path"]
        try:
            deadline = time.time() + settings.job_deadline_sec
            result = analyze_video(video_path, deadline)
            result.update(job_id=job["id"], status="done")
            if result.get("verdict") not in {"violation", "no_violation"} or not isinstance(result.get("violations"), list):
                raise RuntimeError("Pipeline returned an invalid result")
            store.finish(job["id"], result)
        except Exception as exc:
            log.exception("Job %s failed", job["id"])
            store.fail(job["id"], str(exc) or "Analysis failed")
        finally:
            remove_file(video_path)
            for expired_path in store.purge_expired(settings.result_ttl_hours):
                remove_file(expired_path)


if __name__ == "__main__":
    from app.worker_process import main
    main()

