from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from maintainability_lens.schemas import Finding


class Approach(StrEnum):
    SIZE_ONLY = "size-only"
    RATINGS_ONLY = "ratings-only"


class FileFindings(BaseModel):
    findings: list[Finding]
    cost_usd: float | None = None


class RecordedFileFindings(FileFindings):
    file_id: str
    approach: Approach
    repetition: int = Field(ge=0)


def load_recorded_findings(findings_file: Path) -> list[RecordedFileFindings]:
    if not findings_file.exists():
        return []
    return [
        RecordedFileFindings.model_validate_json(line)
        for line in findings_file.read_text().splitlines()
        if line.strip()
    ]


def append_recorded_findings(findings_file: Path, recorded: RecordedFileFindings) -> None:
    findings_file.parent.mkdir(parents=True, exist_ok=True)
    with findings_file.open("a") as output:
        output.write(recorded.model_dump_json() + "\n")
