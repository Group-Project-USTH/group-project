import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path

from maintainability_lens.evaluation.approach_error import ApproachError
from maintainability_lens.evaluation.claude_code_skill import (
    ClaudeCodeOptions,
    decide_with_claude_code,
)
from maintainability_lens.evaluation.deepagents_agent import decide_with_deepagents_agent
from maintainability_lens.evaluation.evaluation_set import EvaluationFile, check_out
from maintainability_lens.evaluation.ratings_only import decide_by_ratings
from maintainability_lens.evaluation.recorded_findings import (
    Approach,
    FileFindings,
    RecordedFileFindings,
    append_recorded_findings,
    load_recorded_findings,
)
from maintainability_lens.evaluation.size_only import decide_by_size

Decider = Callable[[Path, str], FileFindings]

logger = logging.getLogger(__name__)


@dataclass
class ApproachRunSummary:
    recorded_findings: int = 0
    failed_file_ids: list[str] = field(default_factory=list)


def build_decider(approach: Approach, claude_code_options: ClaudeCodeOptions | None) -> Decider:
    if approach is Approach.SIZE_ONLY:
        return decide_by_size
    if approach is Approach.RATINGS_ONLY:
        return decide_by_ratings
    if approach is Approach.DEEPAGENTS_AGENT:
        return decide_with_deepagents_agent
    if claude_code_options is None:
        raise ValueError(f"{approach} needs ClaudeCodeOptions")
    return partial(decide_with_claude_code, claude_code_options)


def findings_file_of(approach: Approach, output_directory: Path) -> Path:
    return output_directory / f"{approach}.jsonl"


def run_approach(
    approach: Approach,
    evaluation_set: list[EvaluationFile],
    checkouts: Path,
    output_directory: Path,
    repetitions: int = 1,
    claude_code_options: ClaudeCodeOptions | None = None,
) -> ApproachRunSummary:
    decide = build_decider(approach, claude_code_options)
    findings_file = findings_file_of(approach, output_directory)
    recorded = {
        (entry.file_id, entry.repetition) for entry in load_recorded_findings(findings_file)
    }
    summary = ApproachRunSummary()
    for repetition in range(repetitions):
        for evaluation_file in evaluation_set:
            if (evaluation_file.file_id, repetition) in recorded:
                continue
            checkout = check_out(evaluation_file, checkouts)
            try:
                file_findings = decide(checkout, evaluation_file.path)
            except ApproachError as error:
                logger.warning("%s failed on %s: %s", approach, evaluation_file.file_id, error)
                summary.failed_file_ids.append(evaluation_file.file_id)
                continue
            append_recorded_findings(
                findings_file,
                RecordedFileFindings(
                    **file_findings.model_dump(),
                    file_id=evaluation_file.file_id,
                    approach=approach,
                    repetition=repetition,
                ),
            )
            summary.recorded_findings += len(file_findings.findings)
    return summary
