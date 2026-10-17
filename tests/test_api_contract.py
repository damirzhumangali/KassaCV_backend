import io
import os
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings


@pytest.fixture(autouse=True)
def setup_env(monkeypatch, tmp_path):
    monkeypatch.setenv("API_KEYS", "test_secret_key")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("WORKER_ENABLED", "false")
    get_settings.cache_clear()


def test_health_public():
    from app.main import app
    with TestClient(app) as client:
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json() == {"status": "ok"}


def test_analyze_unauthorized():
    from app.main import app
    with TestClient(app) as client:
        file_content = b"fake video content"
        res = client.post(
            "/api/v1/analyze",
            files={"file": ("video.mp4", io.BytesIO(file_content), "video/mp4")},
        )
        assert res.status_code == 401


def test_analyze_and_get_job():
    from app.main import app
    with TestClient(app) as client:
        file_content = b"fake video content"
        headers = {"X-API-Key": "test_secret_key"}
        res = client.post(
            "/api/v1/analyze",
            headers=headers,
            files={"file": ("sample.mp4", io.BytesIO(file_content), "video/mp4")},
        )
        assert res.status_code == 202
        data = res.json()
        assert "job_id" in data
        job_id = data["job_id"]

        # Fetch status
        res_job = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
        assert res_job.status_code == 200
        job_data = res_job.json()
        assert job_data["job_id"] == job_id
        assert job_data["status"] == "processing"
