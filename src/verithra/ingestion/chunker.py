"""Split headings first, then fixed word windows. Units are words, not model tokens."""

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path

from verithra.config import VerithraError
from verithra.models import Chunk, Document


def split_sections(text: str) -> list[tuple[str, str]]:
    section = "Overview"
    lines: list[str] = []
    result = []
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        heading = re.match(r"^#{1,6}\s+(.+)$", line) if not fenced else None
        if heading:
            if "\n".join(lines).strip():
                result.append((section, "\n".join(lines).strip()))
            section, lines = heading.group(1).strip(), []
        else:
            lines.append(line)
    if "\n".join(lines).strip():
        result.append((section, "\n".join(lines).strip()))
    return result


def chunk_documents(documents: list[Document], size: int = 120, overlap: int = 20) -> list[Chunk]:
    if size < 10 or not 0 <= overlap < size:
        raise VerithraError("Chunk size must be >= 10 words and 0 <= overlap < size.")
    if len({d.source_id for d in documents}) != len(documents):
        raise VerithraError("Duplicate document source IDs.")
    chunks = []
    for doc in documents:
        for section_number, (section, text) in enumerate(split_sections(doc.text)):
            words = list(re.finditer(r"\S+", text))
            for start in range(0, len(words), size - overlap):
                end = min(start + size, len(words))
                passage = text[words[start].start() : words[end - 1].end()]
                digest = hashlib.sha256(passage.encode()).hexdigest()[:12]
                chunks.append(
                    Chunk(
                        chunk_id=f"{doc.source_id}::{section_number}:{start}::{digest}",
                        source_id=doc.source_id,
                        title=doc.title,
                        section=section,
                        text=passage,
                        source_type=doc.source_type,
                        source_url=doc.source_url,
                        provenance=doc.provenance,
                        source_refs=doc.source_refs,
                    )
                )
                if end == len(words):
                    break
    return chunks


def save_chunks(chunks: list[Chunk], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([asdict(c) for c in chunks], indent=2), encoding="utf-8")


def load_chunks(path: Path) -> list[Chunk]:
    return [Chunk(**record) for record in json.loads(path.read_text(encoding="utf-8"))]
