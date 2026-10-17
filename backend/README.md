# Backend scaffold

This is the API and job-queue scaffold for the local video-analysis service. The video pipeline intentionally fails closed until a real, locally installed detector is configured; it never reports `no_violation` based on an unimplemented analysis.

## Run locally

Use Python 3.11+, install `requirements.txt`, then set a secret key and launch from this directory:

```sh
export API_KEYS='replace-with-a-long-random-secret'
export DATA_DIR="$PWD/data"
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

`GET /health` is public. `POST /api/v1/analyze` accepts multipart field `file`; `GET /api/v1/jobs/{job_id}` returns the job state. Both API routes require `X-API-Key`. Uploads are size limited and deleted after the worker finishes, including failures. Result records expire after `RESULT_TTL_HOURS`.

The local convenience mode runs the worker in a background thread. Docker Compose runs it as a separate process/container. For GPU inference, provision model weights locally. The default pipeline raises a clear failure until implemented. The rules catalog is empty because normative citations must be verified against source documents before use.

Run with Docker Compose using `API_KEYS=... docker compose up --build`.
