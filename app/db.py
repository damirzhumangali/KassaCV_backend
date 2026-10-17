import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, status TEXT NOT NULL, created_at TEXT NOT NULL,
                started_at TEXT, finished_at TEXT, video_path TEXT NOT NULL,
                result_json TEXT, error TEXT
            )""")
            conn.execute("CREATE INDEX IF NOT EXISTS jobs_status_created ON jobs(status, created_at)")
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path, timeout=30)
        conn.row_factory = sqlite3.Row
        return conn

    def recover(self) -> None:
        # A process restart cannot safely resume an in-flight inference.
        with self._connect() as conn:
            conn.execute("UPDATE jobs SET status='failed', error='Worker restarted during processing', finished_at=? WHERE status='processing'", (now_iso(),))
            conn.commit()

    def queue_size(self) -> int:
        with self._connect() as conn:
            return int(conn.execute("SELECT COUNT(*) FROM jobs WHERE status IN ('queued','processing')").fetchone()[0])

    def create(self, job_id: str, video_path: Path) -> None:
        with self._connect() as conn:
            conn.execute("INSERT INTO jobs(id,status,created_at,video_path) VALUES(?,?,?,?)", (job_id, "queued", now_iso(), str(video_path)))
            conn.commit()

    def claim(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute("SELECT * FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
            if row is None:
                conn.commit()
                return None
            conn.execute("UPDATE jobs SET status='processing', started_at=? WHERE id=? AND status='queued'", (now_iso(), row["id"]))
            conn.commit()
            return dict(row)

    def finish(self, job_id: str, result: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE jobs SET status='done', result_json=?, finished_at=? WHERE id=?", (json.dumps(result), now_iso(), job_id))
            conn.commit()

    def fail(self, job_id: str, error: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE jobs SET status='failed', error=?, finished_at=? WHERE id=?", (error[:500], now_iso(), job_id))
            conn.commit()

    def get(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return dict(row) if row else None

    def purge_expired(self, ttl_hours: int) -> list[str]:
        with self._connect() as conn:
            cutoff = datetime.now(timezone.utc).timestamp() - ttl_hours * 3600
            rows = conn.execute("SELECT id, video_path FROM jobs WHERE status IN ('done','failed')").fetchall()
            expired = []
            for row in rows:
                try:
                    finished = datetime.fromisoformat(self.get(row["id"])["finished_at"]).timestamp()
                except (TypeError, ValueError):
                    continue
                if finished < cutoff:
                    expired.append(row["video_path"])
                    conn.execute("DELETE FROM jobs WHERE id=?", (row["id"],))
            conn.commit()
            return expired
