from pathlib import Path

import pytest

from maintainability_lens import agent
from maintainability_lens.evaluation import ApproachError, decide_with_deepagents_agent
from maintainability_lens.schemas import Characteristic, Evidence, Finding, Verdict


def test_the_agent_is_asked_about_the_file_once_per_characteristic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    questions: list[tuple[Path, Characteristic, str | None]] = []

    def fake_evaluate_characteristic(
        target: Path, characteristic: Characteristic, run_id: str, **kwargs: object
    ) -> Finding:
        file = kwargs.get("file")
        questions.append((target, characteristic, file if isinstance(file, str) else None))
        return Finding(
            characteristic=characteristic,
            verdict=Verdict.PASS,
            evidence=[Evidence(file="app.py", line_start=1)],
            rationale="small",
        )

    monkeypatch.setattr(agent, "evaluate_characteristic", fake_evaluate_characteristic)
    monkeypatch.setenv("LLM_MODEL", "openai:test-model")

    file_findings = decide_with_deepagents_agent(tmp_path, "app.py")

    assert questions == [(tmp_path, characteristic, "app.py") for characteristic in Characteristic]
    assert [finding.characteristic for finding in file_findings.findings] == list(Characteristic)
    assert file_findings.model == "openai:test-model"


def test_an_agent_failure_is_an_approach_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def failing_evaluate_characteristic(*args: object, **kwargs: object) -> Finding:
        raise agent.AgentOutputError("no structured answer")

    monkeypatch.setattr(agent, "evaluate_characteristic", failing_evaluate_characteristic)

    with pytest.raises(ApproachError, match="no structured answer"):
        decide_with_deepagents_agent(tmp_path, "app.py")
