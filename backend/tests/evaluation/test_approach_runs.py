from pathlib import Path

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
    assert sorted((entry.file_id, entry.finding.characteristic) for entry in recorded) == sorted(
        (file_id, characteristic) for file_id in ("F01", "F02") for characteristic in Characteristic
    )
    assert {(entry.approach, entry.repetition) for entry in recorded} == {(Approach.SIZE_ONLY, 0)}


def test_a_second_run_skips_files_already_recorded(tmp_path: Path, upstream: Upstream) -> None:
    evaluation_set = make_evaluation_set(upstream)
    run_approach(Approach.RATINGS_ONLY, evaluation_set, tmp_path / "checkouts", tmp_path / "out")

    newly_recorded = run_approach(
        Approach.RATINGS_ONLY, evaluation_set, tmp_path / "checkouts", tmp_path / "out"
    )

    assert newly_recorded == 0
    assert len(load_recorded_findings(tmp_path / "out" / "ratings-only.jsonl")) == 10


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
