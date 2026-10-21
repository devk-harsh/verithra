from dataclasses import dataclass
from pathlib import Path

from verithra.config import VerithraError
from verithra.ingestion.loaders import load_local, load_records
from verithra.models import Document


@dataclass(frozen=True)
class SupportCase:
    case_id: str
    issue: str
    symptoms: list[str]
    root_cause: str
    resolution: list[str]
    source_refs: list[str]
    tags: list[str]
    synthetic: bool

    def as_document(self) -> Document:
        text = (
            f"## Symptoms\n{self.issue}\n"
            + "\n".join(self.symptoms)
            + f"\n\n## Root cause\n{self.root_cause}"
            + "\n\n## Resolution\n"
            + "\n".join(f"- {step}" for step in self.resolution)
            + "\n\nBased on documentation: "
            + ", ".join(self.source_refs)
        )
        return Document(
            self.case_id, self.issue, text, "resolved_case", "", "synthetic_demo", self.source_refs
        )


def load_cases(path: Path, documentation_ids: set[str]) -> list[SupportCase]:
    cases = []
    try:
        for record in load_records(path):
            case = SupportCase(**record)
            if case.synthetic is not True:
                raise ValueError("Demo case must be labelled synthetic.")
            if not all(
                isinstance(value, str) and value.strip()
                for value in [case.case_id, case.issue, case.root_cause]
            ):
                raise ValueError("Empty required fields.")
            if not all(
                isinstance(values, list)
                and values
                and all(isinstance(value, str) and value.strip() for value in values)
                for values in [case.symptoms, case.resolution, case.source_refs, case.tags]
            ):
                raise ValueError("Invalid case lists.")
            if not set(case.source_refs) <= documentation_ids:
                raise ValueError("Unknown documentation reference.")
            cases.append(case)
        if len({c.case_id for c in cases}) != len(cases):
            raise ValueError("Duplicate case ID.")
        return cases
    except (ValueError, TypeError) as exc:
        raise VerithraError("Invalid synthetic support cases or documentation references.") from exc


def load_knowledge(corpus: Path, cases_path: Path | None = None) -> list[Document]:
    documents = load_local(corpus)
    if cases_path:
        ids = {doc.source_id for doc in documents}
        cases = load_cases(cases_path, ids)
        if {c.case_id for c in cases} & ids:
            raise VerithraError("Case IDs collide with documentation IDs.")
        documents.extend(case.as_document() for case in cases)
    return documents
