from dataclasses import dataclass, field


@dataclass(frozen=True)
class Document:
    source_id: str
    title: str
    text: str
    source_type: str = "documentation"
    source_url: str = ""
    provenance: str = "local"
    source_refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    source_id: str
    title: str
    section: str
    text: str
    source_type: str = "documentation"
    source_url: str = ""
    provenance: str = "local"
    source_refs: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SearchHit:
    chunk: Chunk
    score: float


@dataclass(frozen=True)
class ResolutionStep:
    text: str
    citation_ids: list[str]


@dataclass
class Resolution:
    interpretation: str
    likely_cause: str
    cause_citation_ids: list[str]
    recommended_steps: list[ResolutionStep]
    support_status: str
    sources: list[Chunk] = field(default_factory=list)
    retrieved_evidence: list[SearchHit] = field(default_factory=list)
    invalid_citation_ids: list[str] = field(default_factory=list)
    latency_ms: float = 0
    generation_latency_ms: float = 0
    input_tokens: int | None = None
    output_tokens: int | None = None
    context_characters: int = 0
    model: str = ""
    mode: str = "rag"
    abstention_reason: str = ""
    requested_citation_ids: list[str] = field(default_factory=list)
