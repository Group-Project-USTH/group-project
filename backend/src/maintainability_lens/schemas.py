"""Shared data model for the verdicts the agent produces."""

from enum import StrEnum
from typing import Self

from pydantic import BaseModel, Field, computed_field, model_validator


class Characteristic(StrEnum):
    """ISO/IEC 25010 maintainability sub-characteristics."""

    MODULARITY = "modularity"
    REUSABILITY = "reusability"
    ANALYSABILITY = "analysability"
    MODIFIABILITY = "modifiability"
    TESTABILITY = "testability"


class Verdict(StrEnum):
    """Pass, fail or unknown for one characteristic."""

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


class MeasureName(StrEnum):
    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"
    FUNCTION_LINES_OF_CODE = "function_lines_of_code"
    COGNITIVE_COMPLEXITY = "cognitive_complexity"
    PARAMETER_COUNT = "parameter_count"
    FILE_LINES_OF_CODE = "file_lines_of_code"
    DUPLICATED_LINES = "duplicated_lines"
    FILE_FAN_IN = "file_fan_in"


class Measure(BaseModel):
    name: MeasureName
    value: int
    function: str | None = None
    file: str = Field(min_length=1)
    line_start: int = Field(ge=1)
    line_end: int = Field(ge=1)
    is_test_code: bool = False


class ProjectMeasures(BaseModel):
    measures: list[Measure] = Field(default_factory=list)
    unparsed_files: list[str] = Field(default_factory=list)


class ProjectMeasureSummary(BaseModel):
    measures: list[Measure]
    function_count: int = Field(ge=0)
    unparsed_files: list[str]


class SystemProperty(StrEnum):
    UNIT_SIZE = "unit_size"
    UNIT_COMPLEXITY = "unit_complexity"
    UNIT_INTERFACING = "unit_interfacing"
    MODULE_COUPLING = "module_coupling"


class RiskBand(StrEnum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class RiskProfile(BaseModel):
    system_property: SystemProperty
    lines_of_code_per_band: dict[RiskBand, int]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def percentage_per_band(self) -> dict[RiskBand, float]:
        total = sum(self.lines_of_code_per_band.values())
        return {
            band: round(100 * self.lines_of_code_per_band.get(band, 0) / total, 1) if total else 0.0
            for band in RiskBand
        }


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
