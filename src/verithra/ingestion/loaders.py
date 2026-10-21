import json
import re
from pathlib import Path

from verithra.config import VerithraError
from verithra.corpus import load_corpus
from verithra.models import Document


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\x00", "")
    text = "\n".join(line.rstrip() for line in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def load_local(directory: Path) -> list[Document]:
    """Use a manifest for metadata, or stable relative paths for unmanifested MD/TXT."""
    if (directory / "manifest.json").exists():
        docs = load_corpus(directory)
    else:
        docs = []
        for path in sorted(directory.rglob("*")):
            if path.suffix.lower() not in {".md", ".txt"}:
                continue
            relative = path.relative_to(directory).as_posix()
            docs.append(
                Document(
                    source_id=relative,
                    title=path.stem.replace("-", " ").title(),
                    text=path.read_text(encoding="utf-8-sig"),
                )
            )
    return [Document(**{**vars(d), "text": clean_text(d.text)}) for d in docs if clean_text(d.text)]


def load_records(path: Path) -> list[dict]:
    """Read a list of records from JSON or JSONL."""
    try:
        text = path.read_text(encoding="utf-8-sig")
        records = (
            [json.loads(line) for line in text.splitlines() if line.strip()]
            if path.suffix == ".jsonl"
            else json.loads(text)
        )
        if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
            raise ValueError
        return records
    except (ValueError, OSError) as exc:
        raise VerithraError(f"Cannot load record list from {path.name}.") from exc
