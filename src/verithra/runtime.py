from dataclasses import dataclass
from pathlib import Path

from verithra.config import Settings
from verithra.embeddings.client import DemoEmbeddingClient, EmbeddingClient
from verithra.llm.client import LLMClient
from verithra.llm.demo import DemoLLMClient


@dataclass(frozen=True)
class Parameters:
    chunk_size: int = 120
    overlap: int = 20
    top_k: int = 4
    threshold: float = 0.25


def parameters(demo: bool, settings: Settings) -> Parameters:
    if demo:
        return Parameters(chunk_size=40, overlap=0, top_k=6, threshold=0.15)
    return Parameters(top_k=settings.top_k, threshold=settings.evidence_threshold)


def clients(demo: bool, settings: Settings):
    if demo:
        return DemoEmbeddingClient(), DemoLLMClient()
    return EmbeddingClient(settings), LLMClient(settings)


def index_directory(demo: bool) -> Path:
    return Path("data/index/demo" if demo else "data/index/live")
