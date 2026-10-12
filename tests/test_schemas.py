import pytest
from pydantic import ValidationError

from maintain_eval.schemas import Characteristic, Evidence, Finding, Verdict

EVIDENCE = Evidence(file="app.py", line_start=3, line_end=7)


def test_characteristics_are_the_five_iso_25010_subcharacteristics() -> None:
    assert {c.value for c in Characteristic} == {
        "modularity",
        "reusability",
        "analysability",
        "modifiability",
        "testability",
    }


@pytest.mark.parametrize("verdict", [Verdict.PASS, Verdict.FAIL])
def test_agent_pass_or_fail_with_evidence_is_valid(verdict: Verdict) -> None:
    finding = Finding(
        characteristic=Characteristic.MODULARITY,
        verdict=verdict,
        evidence=[EVIDENCE],
        rationale="r",
        source="agent",
    )
    assert finding.evidence == [EVIDENCE]


@pytest.mark.parametrize("verdict", [Verdict.PASS, Verdict.FAIL])
def test_agent_pass_or_fail_without_evidence_is_rejected(verdict: Verdict) -> None:
    with pytest.raises(ValidationError, match="at least one Evidence"):
        Finding(
            characteristic=Characteristic.TESTABILITY,
            verdict=verdict,
            rationale="r",
            source="agent",
        )


def test_agent_unknown_without_evidence_is_valid() -> None:
    finding = Finding(
        characteristic=Characteristic.ANALYSABILITY,
        verdict=Verdict.UNKNOWN,
        rationale="not enough information",
        source="agent",
    )
    assert finding.evidence == []


def test_tool_finding_may_omit_evidence() -> None:
    finding = Finding(
        characteristic=Characteristic.REUSABILITY,
        verdict=Verdict.FAIL,
        rationale="duplication above threshold",
        source="tool:sonarqube",
    )
    assert finding.source == "tool:sonarqube"


@pytest.mark.parametrize("source", ["", "tool:", "human", "tool:has space", "agent2"])
def test_invalid_source_is_rejected(source: str) -> None:
    with pytest.raises(ValidationError):
        Finding(
            characteristic=Characteristic.MODIFIABILITY,
            verdict=Verdict.UNKNOWN,
            rationale="r",
            source=source,
        )


def test_evidence_line_end_before_start_is_rejected() -> None:
    with pytest.raises(ValidationError, match="line_end"):
        Evidence(file="a.py", line_start=10, line_end=2)


@pytest.mark.parametrize("line_start", [0, -1])
def test_evidence_line_start_must_be_positive(line_start: int) -> None:
    with pytest.raises(ValidationError):
        Evidence(file="a.py", line_start=line_start)


def test_evidence_single_line_is_valid() -> None:
    assert Evidence(file="a.py", line_start=1).line_end is None


def test_verdict_parses_from_lowercase_string() -> None:
    finding = Finding.model_validate(
        {
            "characteristic": "testability",
            "verdict": "unknown",
            "rationale": "r",
            "source": "agent",
        }
    )
    assert finding.verdict is Verdict.UNKNOWN
