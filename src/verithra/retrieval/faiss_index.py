"""Exact FAISS inner-product index with a validated positional metadata store."""

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import faiss
import numpy as np

from verithra.config import VerithraError
from verithra.embeddings.client import normalize
from verithra.models import Chunk, SearchHit


class FaissIndex:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray, embedding_model: str):
        vectors = normalize(vectors)
        if len(chunks) != len(vectors) or len({c.chunk_id for c in chunks}) != len(chunks):
            raise VerithraError("FAISS requires one unique chunk per vector row.")
        self.chunks = chunks
        self.embedding_model = embedding_model
        self.config: dict = {}
        self.index = faiss.IndexFlatIP(vectors.shape[1])
        self.index.add(vectors)

    @property
    def dimensions(self) -> int:
        return self.index.d

    def search(self, query: np.ndarray, top_k: int = 4) -> list[SearchHit]:
        if top_k < 1:
            raise VerithraError("top_k must be positive.")
        query = normalize(np.asarray(query).reshape(1, -1))
        if query.shape[1] != self.dimensions:
            raise VerithraError("Query dimension does not match the FAISS index.")
        scores, positions = self.index.search(query, min(top_k, len(self.chunks)))
        return [
            SearchHit(self.chunks[int(position)], float(score))
            for position, score in zip(positions[0], scores[0], strict=True)
            if position >= 0
        ]

    def require_model(self, model: str) -> None:
        if model != self.embedding_model:
            raise VerithraError("Embedding model differs from saved index. Rebuild the index.")

    def save(self, directory: Path, config: dict | None = None) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        binary = faiss.serialize_index(self.index).tobytes()
        self.config = config or self.config
        metadata = {
            "schema_version": 1,
            "embedding_model": self.embedding_model,
            "dimensions": self.dimensions,
            "index_sha256": hashlib.sha256(binary).hexdigest(),
            "config": self.config,
            "chunks": [asdict(c) for c in self.chunks],
        }
        # Replace complete files; metadata is the final commit marker.
        for name, content in [
            ("knowledge.faiss", binary),
            ("metadata.json", json.dumps(metadata, indent=2).encode()),
        ]:
            temporary = directory / (name + ".tmp")
            temporary.write_bytes(content)
            temporary.replace(directory / name)

    @classmethod
    def load(cls, directory: Path) -> "FaissIndex":
        try:
            meta = json.loads((directory / "metadata.json").read_text(encoding="utf-8"))
            binary = (directory / "knowledge.faiss").read_bytes()
            if meta["schema_version"] != 1:
                raise ValueError("schema")
            if hashlib.sha256(binary).hexdigest() != meta["index_sha256"]:
                raise ValueError("checksum")
            index = faiss.deserialize_index(np.frombuffer(binary, dtype=np.uint8).copy())
            chunks = [Chunk(**record) for record in meta["chunks"]]
            if (
                not isinstance(index, faiss.IndexFlatIP)
                or index.ntotal != len(chunks)
                or index.d != meta["dimensions"]
                or not chunks
                or len({c.chunk_id for c in chunks}) != len(chunks)
            ):
                raise ValueError("mapping")
            result = cls.__new__(cls)
            result.index, result.chunks = index, chunks
            result.embedding_model, result.config = meta["embedding_model"], meta["config"]
            return result
        except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
            raise VerithraError("Index is missing or invalid. Run verithra build-index.") from exc
