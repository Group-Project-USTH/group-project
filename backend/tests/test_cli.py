import json
import subprocess
import sys
from pathlib import Path

import pytest

from maintainability_lens import agent, cli
from maintainability_lens.schemas import Characteristic, Evidence, Finding, Verdict

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
    def fake_evaluate_characteristic(
        target: Path, characteristic: Characteristic, run_id: str, **kwargs: object
    ) -> Finding:
        return Finding(
            characteristic=characteristic,
            verdict=Verdict.PASS,
            evidence=[Evidence(file="utils.py", line_start=1)],
            rationale="small and focused",
        )

    monkeypatch.setattr(agent, "evaluate_characteristic", fake_evaluate_characteristic)
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
    def failing_evaluate_characteristic(*args: object, **kwargs: object) -> Finding:
        raise ConnectionError("provider unreachable")

    monkeypatch.setattr(agent, "evaluate_characteristic", failing_evaluate_characteristic)
    assert cli.main(["smoke", "--target", str(SAMPLE)]) == 1
    assert "error: ConnectionError: provider unreachable" in capsys.readouterr().err


def test_measure_prints_project_measures_json(capsys: pytest.CaptureFixture[str]) -> None:
    assert cli.main(["measure", "--target", str(SAMPLE)]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert {
        "name": "cyclomatic_complexity",
        "value": 7,
        "function": "process_order",
        "file": "app.py",
        "line_start": 6,
        "line_end": 25,
        "is_test_code": False,
    } in payload["measures"]
    assert payload["unparsed_files"] == []


def test_measure_missing_target_fails_clearly(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert cli.main(["measure", "--target", str(tmp_path / "nope")]) == 1
    assert "error:" in capsys.readouterr().err


LLM_STACK_MODULES = (
    "deepagents",
    "fastapi",
    "langchain",
    "langchain_core",
    "langchain_openai",
    "langfuse",
    "langgraph",
    "pydantic_settings",
)


def run_cli_without_llm_stack(*args: str) -> subprocess.CompletedProcess[str]:
    script = "\n".join(
        [
            "import sys",
            f"for name in {LLM_STACK_MODULES!r}:",
            "    sys.modules[name] = None",
            "from maintainability_lens import cli",
            f"sys.exit(cli.main({list(args)!r}))",
        ]
    )
    return subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, check=False
    )


def test_measure_runs_without_the_llm_stack() -> None:
    completed = run_cli_without_llm_stack("measure", "--target", str(SAMPLE))

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["unparsed_files"] == []


def test_smoke_without_the_llm_stack_fails_clearly() -> None:
    completed = run_cli_without_llm_stack("smoke", "--target", str(SAMPLE))

    assert completed.returncode == 1
    assert "error: smoke needs the agent dependency group" in completed.stderr


def test_evaluate_set_records_the_findings_of_an_approach(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    upstream = tmp_path / "upstream"
    git = ["git", "-C", str(upstream), "-c", "user.name=test", "-c", "user.email=test@example.com"]
    subprocess.run(["git", "init", "-q", str(upstream)], check=True)
    (upstream / "app.py").write_text("def f(x):\n    return x\n")
    subprocess.run([*git, "add", "."], check=True)
    subprocess.run([*git, "commit", "-q", "-m", "app"], check=True)
    commit = subprocess.run(
        [*git, "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    evaluation_set_file = tmp_path / "evaluation_set.json"
    evaluation_set_file.write_text(
        json.dumps(
            [
                {
                    "file_id": "F01",
                    "project": "upstream",
                    "licence": "MIT",
                    "repository_url": upstream.as_uri(),
                    "commit": commit,
                    "path": "app.py",
                    "url": upstream.as_uri(),
                }
            ]
        )
    )

    code = cli.main(
        [
            "evaluate-set",
            "--approach",
            "size-only",
            "--evaluation-set",
            str(evaluation_set_file),
            "--checkouts",
            str(tmp_path / "checkouts"),
            "--output",
            str(tmp_path / "out"),
        ]
    )

    assert code == 0
    assert len((tmp_path / "out" / "size-only.jsonl").read_text().splitlines()) == 5
    assert "5 new Findings" in capsys.readouterr().out
