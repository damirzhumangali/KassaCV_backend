from functools import lru_cache
from pathlib import Path
import os


class Settings:
    def __init__(self) -> None:
        self.data_dir = Path(os.getenv("DATA_DIR", "/data"))
        self.upload_dir = self.data_dir / "uploads"
        self.db_path = Path(os.getenv("DB_PATH", str(self.data_dir / "jobs.sqlite3")))
        self.rules_path = Path(os.getenv("RULES_PATH", str(Path(__file__).parent / "rules" / "rules_catalog.json")))
        self.max_upload_mb = int(os.getenv("MAX_UPLOAD_MB", "500"))
        self.max_queue_size = int(os.getenv("MAX_QUEUE_SIZE", "50"))
        self.result_ttl_hours = int(os.getenv("RESULT_TTL_HOURS", "24"))
        self.job_deadline_sec = int(os.getenv("JOB_DEADLINE_SEC", "240"))
        self.api_keys = tuple(k.strip() for k in os.getenv("API_KEYS", "").split(",") if k.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()
