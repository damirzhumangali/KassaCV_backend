from fastapi import APIRouter, Depends, HTTPException, Request

from app.auth import require_api_key
from app.schemas import JobDone, JobFailed, JobProcessing

router = APIRouter(dependencies=[Depends(require_api_key)])


@router.get("/jobs/{job_id}", response_model=JobProcessing | JobFailed | JobDone)
def get_job(job_id: str, request: Request):
    row = request.app.state.store.get(job_id)
    if row is None:
        raise HTTPException(404, "Job not found")
    if row["status"] in {"queued", "processing"}:
        return JobProcessing(job_id=job_id, status="processing")
    if row["status"] == "failed":
        return JobFailed(job_id=job_id, status="failed", error=row["error"] or "Analysis failed")
    import json
    return json.loads(row["result_json"])
