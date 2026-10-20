"""Shared data model for the verdicts the agent produces."""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, model_validator


class Characteristic(StrEnum):
    """ISO/IEC 25010 maintainability sub-characteristics."""

    MODULARITY = "modularity"
    REUSABILITY = "reusability"
    ANALYSABILITY = "analysability"
    MODIFIABILITY = "modifiability"
    TESTABILITY = "testability"


class Verdict(StrEnum):
    """Outcome for one characteristic."""

    PASS = "pass"
    FAIL = "fail"
    UNKNOWN = "unknown"


class Evidence(BaseModel):
    """A file location backing a verdict."""

    file: str = Field(min_length=1, description="Path relative to the analysed project root.")
    line_start: int = Field(ge=1)
    line_end: int | None = Field(default=None, ge=1)
    snippet: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _check_line_range(self) -> Self:
        if self.line_end is not None and self.line_end < self.line_start:
            raise ValueError("line_end must be >= line_start")
        return self


class Finding(BaseModel):
    """One verdict for one characteristic."""

    characteristic: Characteristic
    verdict: Verdict
    evidence: list[Evidence] = Field(default_factory=list)
    rationale: str

    @model_validator(mode="after")
    def _pass_or_fail_needs_evidence(self) -> Self:
        if self.verdict is not Verdict.UNKNOWN and not self.evidence:
            raise ValueError("PASS/FAIL verdicts must cite at least one Evidence")
        return self
