"""Load environment configuration once; never print credentials."""

import math
import os
from dataclasses import dataclass, field

from dotenv import load_dotenv


class VerithraError(Exception):
    """An actionable application error safe to show to the user."""


@dataclass(frozen=True)
class Settings:
    api_key: str = field(default="", repr=False)
    llm_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    top_k: int = 4
    evidence_threshold: float = 0.25
    max_context_characters: int = 160000

    def __post_init__(self):
        if self.top_k < 1 or self.max_context_characters < 1000:
            raise VerithraError(
                "top_k must be positive and context budget at least 1000 characters."
            )
        if not math.isfinite(self.evidence_threshold) or not 0 <= self.evidence_threshold <= 1:
            raise VerithraError("Evidence threshold must be finite and between 0 and 1.")

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        try:
            return cls(
                api_key=os.getenv("OPENAI_API_KEY", "").strip(),
                llm_model=os.getenv("VERITHRA_LLM_MODEL", "gpt-4.1-mini"),
                embedding_model=os.getenv("VERITHRA_EMBEDDING_MODEL", "text-embedding-3-small"),
                top_k=int(os.getenv("VERITHRA_TOP_K", "4")),
                evidence_threshold=float(os.getenv("VERITHRA_EVIDENCE_THRESHOLD", "0.25")),
                max_context_characters=int(os.getenv("VERITHRA_MAX_CONTEXT_CHARACTERS", "160000")),
            )
        except ValueError as exc:
            raise VerithraError("Invalid numeric Verithra environment configuration.") from exc

    def require_api_key(self) -> str:
        if not self.api_key:
            raise VerithraError("Set OPENAI_API_KEY in your environment or an ignored .env file.")
        return self.api_key
