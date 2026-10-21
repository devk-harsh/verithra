import time

from verithra.config import VerithraError
from verithra.models import Chunk, Document, Resolution, SearchHit
from verithra.rag.generator import parse_resolution
from verithra.rag.grounding import enforce_grounding, sufficient_evidence
from verithra.rag.prompts import INSTRUCTIONS, RESOLUTION_SCHEMA, build_prompt


def abstention(question: str) -> Resolution:
    return Resolution(
        interpretation=question,
        likely_cause="",
        cause_citation_ids=[],
        recommended_steps=[],
        support_status="INSUFFICIENT_EVIDENCE",
    )


class Pipeline:
    def __init__(
        self,
        index,
        embedder,
        generator,
        top_k: int = 4,
        threshold: float = 0.25,
        max_context_characters: int = 160000,
    ):
        self.index, self.embedder, self.generator = index, embedder, generator
        self.top_k = top_k
        self.threshold, self.max_context_characters = threshold, max_context_characters
        if index is not None:
            index.require_model(embedder.model)

    def _generate(self, question: str, evidence: list[Chunk]) -> Resolution:
        if not evidence:
            return abstention(question)
        prompt = build_prompt(question, evidence)
        if len(prompt) > self.max_context_characters:
            raise VerithraError("Context exceeds the configured budget. Reduce corpus or top-k.")
        generation = self.generator.generate(INSTRUCTIONS, prompt, RESOLUTION_SCHEMA)
        result = enforce_grounding(parse_resolution(generation.text, evidence), question)
        result.generation_latency_ms = generation.latency_ms
        result.input_tokens, result.output_tokens = (
            generation.input_tokens,
            generation.output_tokens,
        )
        result.model = generation.model
        result.context_characters = sum(len(c.text) for c in evidence)
        return result

    def ask(self, question: str) -> Resolution:
        if not question.strip():
            raise VerithraError("Describe a non-empty technical issue.")
        started = time.perf_counter()
        query = self.embedder.embed([question])[0]
        hits = self.index.search(query, self.top_k)
        if sufficient_evidence(hits, self.threshold):
            eligible = [h.chunk for h in hits if h.score >= self.threshold]
            result = self._generate(question, eligible)
        else:
            result = abstention(question)
            result.abstention_reason = "weak_retrieval"
        result.retrieved_evidence = hits
        result.latency_ms = (time.perf_counter() - started) * 1000
        result.model = self.generator.model
        return result

    def full_context(self, question: str, documents: list[Document]) -> Resolution:
        if not question.strip():
            raise VerithraError("Describe a non-empty technical issue.")
        started = time.perf_counter()
        evidence = [
            Chunk(
                d.source_id + "::full",
                d.source_id,
                d.title,
                "Complete source record",
                d.text,
                d.source_type,
                d.source_url,
                d.provenance,
                d.source_refs,
            )
            for d in documents
        ]
        result = self._generate(question, evidence)
        result.retrieved_evidence = [SearchHit(c, 0) for c in evidence]
        result.latency_ms = (time.perf_counter() - started) * 1000
        result.mode = "full_context"
        return result
