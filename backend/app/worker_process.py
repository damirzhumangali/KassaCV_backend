import logging
import signal
import threading

from app.config import get_settings
from app.db import JobStore
from app.worker import worker_loop


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    store = JobStore(settings.db_path)
    store.recover()
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())
    signal.signal(signal.SIGINT, lambda *_: stop.set())
    worker_loop(store, stop)


if __name__ == "__main__":
    main()
