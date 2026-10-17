import pytest
from pydantic import ValidationError
from app.schemas import JobDone, JobFailed, JobProcessing, Violation, EvidenceFrame


def test_violation_schema():
    v = Violation(
        type="Невыдача чека",
        timecode_sec=12.5,
        description="Тестовое описание",
        evidence_frames=[EvidenceFrame(timestamp_sec=12.5, image_base64="dGVzdA==")],
        rule_id="R-01",
        source="Налоговый кодекс",
        clause="ст. 166",
        confidence=0.95,
    )
    assert v.timecode_sec == 12.5
    assert v.confidence == 0.95


def test_job_done_schema():
    job = JobDone(
        job_id="test1234",
        status="done",
        verdict="no_violation",
        violations=[],
    )
    assert job.verdict == "no_violation"

    with pytest.raises(ValidationError):
        JobDone(
            job_id="test1234",
            status="done",
            verdict="invalid_verdict",  # Only 'violation' or 'no_violation' allowed
            violations=[],
        )
