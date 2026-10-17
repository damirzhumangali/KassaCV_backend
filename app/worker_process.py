import logging
import os
import signal
import sys
import threading

from app.config import get_settings
from app.db import JobStore
from app.worker import worker_loop

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [worker] %(name)s: %(message)s"
)
log = logging.getLogger("worker_process")


def main() -> None:
    settings = get_settings()
    log.info("Starting standalone worker process with data dir: %s", settings.data_dir)
    store = JobStore(settings.db_path)
    store.recover()

    stop_event = threading.Event()

    def _handle_signal(sig, frame):
        log.info("Received signal %s, initiating graceful shutdown...", sig)
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        worker_loop(store, stop_event)
    except Exception:
        log.exception("Fatal error in worker process")
        sys.exit(1)

    log.info("Worker process exited cleanly")


if __name__ == "__main__":
    main()
