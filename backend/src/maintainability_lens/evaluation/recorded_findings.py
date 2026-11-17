from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field

from maintainability_lens.schemas import Finding


class Approach(StrEnum):
    SIZE_ONLY = "size-only"
    RATINGS_ONLY = "ratings-only"


class RecordedFinding(BaseModel):
    file_id: str
    approach: Approach
    repetition: int = Field(ge=0)
    finding: Finding
    cost_usd: float | None = None


def load_recorded_findings(findings_file: Path) -> list[RecordedFinding]:
    if not findings_file.exists():
        return []
    return [
        RecordedFinding.model_validate_json(line)
        for line in findings_file.read_text().splitlines()
        if line.strip()
    ]


def append_recorded_findings(findings_file: Path, recorded: list[RecordedFinding]) -> None:
    findings_file.parent.mkdir(parents=True, exist_ok=True)
    with findings_file.open("a") as output:
        output.writelines(entry.model_dump_json() + "\n" for entry in recorded)
