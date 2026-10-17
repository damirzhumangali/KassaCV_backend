import logging
from typing import Any
from app.pipeline.events import CandidateEvent
from app.pipeline.evidence import extract_evidence_frames
from app.pipeline.sampling import VideoFrame
from app.pipeline.vlm import VLMVerifier

log = logging.getLogger(__name__)


def aggregate_and_format_verdict(
    candidates: list[CandidateEvent],
    sampled_frames: list[VideoFrame],
    catalog: dict[str, dict[str, Any]],
    vlm_verifier: VLMVerifier,
    confidence_threshold: float = 0.5,
) -> dict[str, Any]:
    """Merges candidate events, verifies through VLM/rules, and formats final verdict."""
    if not candidates:
        return {
            "verdict": "no_violation",
            "violations": [],
        }

    # 1. Merge adjacent candidates of the same rule type (within 2 seconds)
    merged_candidates: list[CandidateEvent] = []
    sorted_candidates = sorted(candidates, key=lambda c: (c.rule_id, c.t_start))

    for cand in sorted_candidates:
        if not merged_candidates:
            merged_candidates.append(cand)
            continue
        prev = merged_candidates[-1]
        if prev.rule_id == cand.rule_id and (cand.t_start - prev.t_end) <= 2.0:
            # Extend interval and take max score
            prev.t_end = max(prev.t_end, cand.t_end)
            prev.score = max(prev.score, cand.score)
        else:
            merged_candidates.append(cand)

    violations: list[dict[str, Any]] = []

    # 2. Verify and build evidence for each merged event
    for cand in merged_candidates:
        confirmed, description, conf = vlm_verifier.verify_and_describe(cand, sampled_frames)
        if not confirmed or conf < confidence_threshold:
            continue

        rule = catalog.get(cand.rule_id, {})
        evidence_frames = extract_evidence_frames(cand, sampled_frames)

        primary_timecode = evidence_frames[0]["timestamp_sec"] if evidence_frames else round(cand.t_start, 2)

        violations.append({
            "type": cand.rule_type,
            "timecode_sec": primary_timecode,
            "description": description,
            "evidence_frames": evidence_frames,
            "rule_id": cand.rule_id,
            "source": rule.get("source"),
            "clause": rule.get("clause"),
            "confidence": round(conf, 2),
        })

    verdict = "violation" if len(violations) > 0 else "no_violation"

    return {
        "verdict": verdict,
        "violations": violations,
    }
