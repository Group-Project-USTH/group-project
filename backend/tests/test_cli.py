import json
from pathlib import Path

import pytest

from maintain_eval import cli
from maintain_eval.schemas import Characteristic, Evidence, Finding, Verdict

SAMPLE = Path(__file__).parent / "fixtures" / "sample_project"


def test_smoke_without_llm_model_fails_clearly(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["smoke", "--target", str(SAMPLE)]) == 1
    assert "LLM_MODEL is not set" in capsys.readouterr().err


def test_smoke_missing_target_fails_clearly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["smoke", "--target", str(tmp_path / "nope")]) == 1
    assert "error:" in capsys.readouterr().err


def test_smoke_prints_finding_json(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fake_run_smoke(
        target: Path, characteristic: Characteristic, run_id: str, **kwargs: object
    ) -> Finding:
        return Finding(
            characteristic=characteristic,
            verdict=Verdict.PASS,
            evidence=[Evidence(file="utils.py", line_start=1)],
            rationale="small and focused",
        )

    monkeypatch.setattr(cli, "run_smoke", fake_run_smoke)
    code = cli.main(
        ["smoke", "--target", str(SAMPLE), "--characteristic", "testability", "--run-id", "r9"]
    )
    out = capsys.readouterr()
    assert code == 0
    assert "run_id=r9" in out.err
    payload = json.loads(out.out)
    assert payload["characteristic"] == "testability"
    assert payload["verdict"] == "pass"


def test_unknown_characteristic_is_rejected() -> None:
    with pytest.raises(SystemExit):
        cli.main(["smoke", "--target", str(SAMPLE), "--characteristic", "speed"])


def test_unexpected_errors_print_cleanly(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failing_run_smoke(*args: object, **kwargs: object) -> Finding:
        raise ConnectionError("provider unreachable")

    monkeypatch.setattr(cli, "run_smoke", failing_run_smoke)
    assert cli.main(["smoke", "--target", str(SAMPLE)]) == 1
    assert "error: ConnectionError: provider unreachable" in capsys.readouterr().err
