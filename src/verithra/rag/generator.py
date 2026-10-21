"""Parse model output and resolve citations only against supplied evidence."""

import json

from verithra.config import VerithraError
from verithra.models import Chunk, Resolution, ResolutionStep


def parse_resolution(text: str, chunks: list[Chunk]) -> Resolution:
    try:
        raw = json.loads(text)
        if raw["support_status"] not in {"SUPPORTED", "INSUFFICIENT_EVIDENCE"}:
            raise ValueError("status")
        if not all(isinstance(raw[key], str) for key in ["interpretation", "likely_cause"]):
            raise ValueError("strings")
        steps = [ResolutionStep(**step) for step in raw["recommended_steps"]]
        citation_lists = [raw["cause_citation_ids"]] + [step.citation_ids for step in steps]
        if not all(
            isinstance(ids, list) and all(isinstance(identifier, str) for identifier in ids)
            for ids in citation_lists
        ) or not all(isinstance(step.text, str) for step in steps):
            raise ValueError("citations")
        known = {chunk.chunk_id: chunk for chunk in chunks}
        requested = list(dict.fromkeys(i for ids in citation_lists for i in ids))
        return Resolution(
            interpretation=raw["interpretation"],
            likely_cause=raw["likely_cause"],
            cause_citation_ids=[i for i in raw["cause_citation_ids"] if i in known],
            recommended_steps=[
                ResolutionStep(step.text, [i for i in step.citation_ids if i in known])
                for step in steps
            ],
            support_status=raw["support_status"],
            sources=[known[i] for i in requested if i in known],
            invalid_citation_ids=[i for i in requested if i not in known],
            requested_citation_ids=requested,
        )
    except (ValueError, KeyError, TypeError) as exc:
        raise VerithraError(
            "Model response was malformed. No unvalidated answer is displayed."
        ) from exc
