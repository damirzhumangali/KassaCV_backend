import logging
from typing import Any
from app.pipeline.events import CandidateEvent
from app.pipeline.sampling import VideoFrame

log = logging.getLogger(__name__)


class VLMVerifier:
    """Verifies candidate violations and generates structured descriptions using local VLM or factual fallbacks."""

    def __init__(self, catalog: dict[str, dict[str, Any]], device: str = "cpu") -> None:
        self.catalog = catalog
        self.device = device
        self.model = None

    def verify_and_describe(
        self,
        candidate: CandidateEvent,
        frames: list[VideoFrame],
    ) -> tuple[bool, str, float]:
        """
        Returns (confirmed: bool, description: str, updated_confidence: float).
        Formula for description:
        1. Observable facts
        2. Why this may indicate a violation (catalog['interpretation'])
        3. Normative citation (catalog['source'], catalog['clause'])
        """
        rule = self.catalog.get(candidate.rule_id, {})
        interpretation = rule.get("interpretation", "Может указывать на нарушение регламента кассового узла.")
        source = rule.get("source", "Нормативный регламент")
        clause = rule.get("clause", "")
        rule_tag = f"({candidate.rule_id}: {source}, {clause})" if clause else f"({candidate.rule_id}: {source})"

        # Part 1: Observable factual summary
        fact_summary = candidate.context.get("details")
        if not fact_summary:
            fact_summary = f"В интервале с {candidate.t_start:.1f}с по {candidate.t_end:.1f}с зафиксированы визуальные признаки события '{candidate.rule_type}'."

        # Structured 3-part description
        full_description = f"{fact_summary} {interpretation} {rule_tag}"

        # In offline/fast mode or without loaded weights, confirm candidate using rule engine confidence
        confirmed = candidate.score >= 0.5
        return confirmed, full_description, candidate.score
