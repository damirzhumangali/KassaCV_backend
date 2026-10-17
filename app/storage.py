from pathlib import Path
import uuid


def new_job_id() -> str:
    return uuid.uuid4().hex[:12]


def remove_file(path: str | Path) -> None:
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass
