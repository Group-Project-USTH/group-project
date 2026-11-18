from pathlib import Path

import pytest
from fake_claude import FakeClaude, answer_every_characteristic
from upstream_repository import Upstream

from maintainability_lens.evaluation import (
    Approach,
    EvaluationFile,
    load_recorded_findings,
    run_approach,
)
from maintainability_lens.schemas import Characteristic


def make_evaluation_set(upstream: Upstream) -> list[EvaluationFile]:
    upstream.commit("small.py", "def f(x):\n    return x\n")
    commit = upstream.commit("other.py", "def g(x):\n    return x\n")
    return [
        upstream.describe(commit, "small.py", file_id="F01"),
        upstream.describe(commit, "other.py", file_id="F02"),
    ]


def test_a_run_records_one_finding_per_file_and_characteristic(
    tmp_path: Path, upstream: Upstream
) -> None:
    evaluation_set = make_evaluation_set(upstream)

    run_approach(Approach.SIZE_ONLY, evaluation_set, tmp_path / "checkouts", tmp_path / "out")

    recorded = load_recorded_findings(tmp_path / "out" / "size-only.jsonl")
    assert sorted(
        (entry.file_id, finding.characteristic) for entry in recorded for finding in entry.findings
    ) == sorted(
        (file_id, characteristic) for file_id in ("F01", "F02") for characteristic in Characteristic
    )
    assert {(entry.approach, entry.repetition) for entry in recorded} == {(Approach.SIZE_ONLY, 0)}


def test_a_second_run_skips_files_already_recorded(tmp_path: Path, upstream: Upstream) -> None:
    evaluation_set = make_evaluation_set(upstream)
    run_approach(Approach.RATINGS_ONLY, evaluation_set, tmp_path / "checkouts", tmp_path / "out")

    summary = run_approach(
        Approach.RATINGS_ONLY, evaluation_set, tmp_path / "checkouts", tmp_path / "out"
    )

    assert summary.recorded_findings == 0
    assert len(load_recorded_findings(tmp_path / "out" / "ratings-only.jsonl")) == 2


def test_repetitions_record_each_file_once_per_repetition(
    tmp_path: Path, upstream: Upstream
) -> None:
    evaluation_set = make_evaluation_set(upstream)

    run_approach(
        Approach.SIZE_ONLY,
        evaluation_set,
        tmp_path / "checkouts",
        tmp_path / "out",
        repetitions=3,
    )

    recorded = load_recorded_findings(tmp_path / "out" / "size-only.jsonl")
    assert sorted({(entry.file_id, entry.repetition) for entry in recorded}) == [
        (file_id, repetition) for file_id in ("F01", "F02") for repetition in range(3)
    ]


def test_the_claude_code_skill_needs_its_options(tmp_path: Path, upstream: Upstream) -> None:
    evaluation_set = make_evaluation_set(upstream)

    with pytest.raises(ValueError, match="claude-code-skill"):
        run_approach(
            Approach.CLAUDE_CODE_SKILL, evaluation_set, tmp_path / "checkouts", tmp_path / "out"
        )


def test_a_failed_file_is_reported_and_left_for_the_next_run(
    tmp_path: Path,
    upstream: Upstream,
    fake_claude: FakeClaude,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    evaluation_set = make_evaluation_set(upstream)
    answer_every_characteristic(fake_claude)
    monkeypatch.setenv("FAKE_CLAUDE_FAIL_FOR", "other.py")

    summary = run_approach(
        Approach.CLAUDE_CODE_SKILL,
        evaluation_set,
        tmp_path / "checkouts",
        tmp_path / "out",
        claude_code_options=fake_claude.options(tmp_path),
    )

    recorded = load_recorded_findings(tmp_path / "out" / "claude-code-skill.jsonl")
    assert [entry.file_id for entry in recorded] == ["F01"]
    assert [entry.cost_usd for entry in recorded] == [0.42]
    assert summary.failed_file_ids == ["F02"]
    assert summary.recorded_findings == 5
