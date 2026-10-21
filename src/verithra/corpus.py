"""The initial manifest-backed corpus, shared by baseline and later ingestion."""

import json
from pathlib import Path

from verithra.config import VerithraError
from verithra.models import Document


def load_corpus(directory: Path) -> list[Document]:
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    documents = []
    for entry in manifest:
        target = (directory / entry["path"]).resolve()
        if not target.is_relative_to(directory.resolve()):
            raise VerithraError("Manifest paths must stay within the corpus directory.")
        documents.append(
            Document(
                source_id=entry["source_id"],
                title=entry["title"],
                text=target.read_text(encoding="utf-8"),
                source_type=entry.get("source_type", "documentation"),
                source_url=entry.get("source_url", ""),
                provenance=entry.get("provenance", "local"),
            )
        )
    if not documents or len({d.source_id for d in documents}) != len(documents):
        raise VerithraError("Corpus must have non-empty, unique source records.")
    return documents
