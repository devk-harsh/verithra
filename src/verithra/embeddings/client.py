import hashlib
import re
from pathlib import Path

import numpy as np
from openai import APIError, OpenAI

from verithra.config import Settings, VerithraError


def normalize(vectors: np.ndarray) -> np.ndarray:
    vectors = np.asarray(vectors, dtype=np.float32)
    if vectors.ndim != 2 or not vectors.shape[0] or not vectors.shape[1]:
        raise VerithraError("Expected a non-empty vector matrix.")
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    if not np.isfinite(vectors).all() or np.any(norms == 0):
        raise VerithraError("Embedding contains non-finite values or a zero vector.")
    return np.ascontiguousarray(vectors / norms, dtype=np.float32)


class EmbeddingClient:
    def __init__(self, settings: Settings, sdk=None):
        self.model = settings.embedding_model
        self.sdk = sdk or OpenAI(api_key=settings.require_api_key(), timeout=45, max_retries=2)

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts or any(not t.strip() for t in texts):
            raise VerithraError("Embeddings require non-empty text.")
        rows = []
        try:
            for start in range(0, len(texts), 64):
                batch = texts[start : start + 64]
                response = self.sdk.embeddings.create(
                    model=self.model, input=batch, encoding_format="float"
                )
                records = sorted(response.data, key=lambda item: item.index)
                if [r.index for r in records] != list(range(len(batch))):
                    raise VerithraError("Embedding provider returned an invalid row mapping.")
                rows.extend(record.embedding for record in records)
        except APIError as exc:
            raise VerithraError(
                "Embedding request failed. Check key, quota and model access."
            ) from exc
        return normalize(np.asarray(rows, dtype=np.float32))


STOP_WORDS = frozenset(
    "a an the to of and or for in on is are was be it this that with from as at by "
    "my i how why what can do does when if then has have your our me we you".split()
)


def terms(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9_]+", text.lower()) if word not in STOP_WORDS]


class DemoEmbeddingClient:
    """Deterministic hashed lexical vectors. NOT learned semantic embeddings."""

    model = "demo-hash-v1-512"
    dimensions = 512

    def embed(self, texts: list[str]) -> np.ndarray:
        matrix = np.zeros((len(texts), self.dimensions), dtype=np.float32)
        for row, text in enumerate(texts):
            for word in terms(text):
                digest = hashlib.sha256(word.encode()).digest()
                column = int.from_bytes(digest[:4], "little") % self.dimensions
                matrix[row, column] += 1
        return normalize(matrix)


def cached_embeddings(texts: list[str], client, directory: Path) -> np.ndarray:
    """Cache derived vectors by provider model + exact embedding input."""
    directory.mkdir(parents=True, exist_ok=True)
    paths = [
        directory / (hashlib.sha256((client.model + "\0" + text).encode()).hexdigest() + ".npy")
        for text in texts
    ]
    missing = {path: text for path, text in zip(paths, texts, strict=True) if not path.exists()}
    if missing:
        vectors = client.embed(list(missing.values()))
        for path, vector in zip(missing, vectors, strict=True):
            np.save(path, vector, allow_pickle=False)
    try:
        return normalize(np.stack([np.load(path, allow_pickle=False) for path in paths]))
    except (ValueError, OSError) as exc:
        raise VerithraError("Embedding cache is corrupt. Remove data/cache and rebuild.") from exc


def embedding_text(chunk) -> str:
    return f"{chunk.title}\n{chunk.section}\n{chunk.text}"
