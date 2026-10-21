"""An explicit offline extractive fixture; no language model or semantic claims."""

import json
import time

from verithra.embeddings.client import terms
from verithra.llm.client import Generation


class DemoLLMClient:
    model = "demo-extractive-v1"

    def generate(self, instructions: str, user_input: str, schema=None) -> Generation:
        started = time.perf_counter()
        payload = json.loads(user_input)
        question_terms = set(terms(payload["question"]))
        candidates = payload["evidence"]

        # Fixed rule: prefer the supplied passage covering most query terms.
        def overlap(record):
            return len(question_terms & set(terms(record["title"] + " " + record["text"])))

        best = max(candidates, key=overlap) if candidates else None
        supported = best is not None and overlap(best) >= 2
        response = {
            "interpretation": payload["question"],
            "likely_cause": best["text"] if supported else "",
            "cause_citation_ids": [best["chunk_id"]] if supported else [],
            "recommended_steps": [{"text": best["text"], "citation_ids": [best["chunk_id"]]}]
            if supported
            else [],
            "support_status": "SUPPORTED" if supported else "INSUFFICIENT_EVIDENCE",
        }
        return Generation(
            json.dumps(response), (time.perf_counter() - started) * 1000, model=self.model
        )
