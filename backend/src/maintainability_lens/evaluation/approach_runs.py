from collections.abc import Callable
from pathlib import Path

from maintainability_lens.evaluation.evaluation_set import EvaluationFile, check_out
from maintainability_lens.evaluation.ratings_only import decide_by_ratings
from maintainability_lens.evaluation.recorded_findings import (
    Approach,
    RecordedFinding,
    append_recorded_findings,
    load_recorded_findings,
)
from maintainability_lens.evaluation.size_only import decide_by_size
from maintainability_lens.schemas import Finding

DECIDERS: dict[Approach, Callable[[Path, str], list[Finding]]] = {
    Approach.SIZE_ONLY: decide_by_size,
    Approach.RATINGS_ONLY: decide_by_ratings,
}


def findings_file_of(approach: Approach, output_directory: Path) -> Path:
    return output_directory / f"{approach}.jsonl"


def run_approach(
    approach: Approach,
    evaluation_set: list[EvaluationFile],
    checkouts: Path,
    output_directory: Path,
    repetitions: int = 1,
) -> int:
    findings_file = findings_file_of(approach, output_directory)
    recorded = {
        (entry.file_id, entry.repetition) for entry in load_recorded_findings(findings_file)
    }
    newly_recorded = 0
    for repetition in range(repetitions):
        for evaluation_file in evaluation_set:
            if (evaluation_file.file_id, repetition) in recorded:
                continue
            checkout = check_out(evaluation_file, checkouts)
            findings = DECIDERS[approach](checkout, evaluation_file.path)
            append_recorded_findings(
                findings_file,
                [
                    RecordedFinding(
                        file_id=evaluation_file.file_id,
                        approach=approach,
                        repetition=repetition,
                        finding=finding,
                    )
                    for finding in findings
                ],
            )
            newly_recorded += len(findings)
    return newly_recorded
