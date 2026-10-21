"""Transparent gates; scores are similarities, never probabilities."""

import math
import re

from verithra.config import VerithraError
from verithra.models import Resolution, SearchHit

ABSTENTION_MESSAGE = (
    "I don't have sufficient evidence in the available knowledge base to resolve this issue."
)


def sufficient_evidence(hits: list[SearchHit], threshold: float, minimum: int = 1) -> bool:
    if not math.isfinite(threshold) or not 0 <= threshold <= 1 or minimum < 1:
        raise VerithraError("Invalid evidence-sufficiency settings.")
    return sum(math.isfinite(h.score) and h.score >= threshold for h in hits) >= minimum


def enforce_grounding(result: Resolution, question: str) -> Resolution:
    """Fail closed; ID membership cannot establish semantic entailment."""
    reason = ""
    if result.support_status != "SUPPORTED":
        reason = "model_abstained"
    elif result.invalid_citation_ids:
        reason = "invalid_citations"
    elif (
        not result.likely_cause.strip()
        or not result.cause_citation_ids
        or not result.recommended_steps
        or any(not step.text.strip() or not step.citation_ids for step in result.recommended_steps)
    ):
        reason = "uncited_or_empty_claims"
    elif any(
        re.search(r"\[[^\]\n]+\]", text)
        for text in [result.interpretation, result.likely_cause]
        + [step.text for step in result.recommended_steps]
    ):
        reason = "inline_citations_not_allowed"
    if reason:
        result.support_status = "INSUFFICIENT_EVIDENCE"
        result.interpretation = question
        result.likely_cause = ""
        result.cause_citation_ids = []
        result.recommended_steps = []
        result.sources = []
        result.abstention_reason = reason
    return result
