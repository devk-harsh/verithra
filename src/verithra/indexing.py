from pathlib import Path

from verithra.config import VerithraError
from verithra.embeddings.client import cached_embeddings, embedding_text
from verithra.ingestion.chunker import chunk_documents, save_chunks
from verithra.retrieval.faiss_index import FaissIndex
from verithra.support.cases import load_knowledge


def build_index(
    corpus: Path,
    directory: Path,
    embedder,
    chunk_size: int = 120,
    overlap: int = 20,
    cases_path: Path | None = None,
    processed_path: Path | None = None,
) -> FaissIndex:
    chunks = chunk_documents(load_knowledge(corpus, cases_path), chunk_size, overlap)
    if not chunks:
        raise VerithraError("No source documents were found.")
    vectors = cached_embeddings([embedding_text(c) for c in chunks], embedder, Path("data/cache"))
    index = FaissIndex(chunks, vectors, embedder.model)
    index.save(directory, {"chunk_size": chunk_size, "overlap": overlap})
    if processed_path:
        save_chunks(chunks, processed_path)
    return index
