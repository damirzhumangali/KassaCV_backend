from typing import Literal
from pydantic import BaseModel, Field


class EvidenceFrame(BaseModel):
    timestamp_sec: float
    image_base64: str


class Violation(BaseModel):
    type: str
    timecode_sec: float
    description: str
    evidence_frames: list[EvidenceFrame] = Field(default_factory=list)
    rule_id: str | None = None
    source: str | None = None
    clause: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)


class JobAccepted(BaseModel):
    job_id: str


class JobProcessing(BaseModel):
    job_id: str
    status: Literal["processing"]


class JobFailed(BaseModel):
    job_id: str
    status: Literal["failed"]
    error: str


class JobDone(BaseModel):
    job_id: str
    status: Literal["done"]
    verdict: Literal["violation", "no_violation"]
    violations: list[Violation]
