import pytest

from maintainability_lens.evaluation import (
    Approach,
    RaterVerdict,
    RecordedFileFindings,
    score_evaluation,
)
from maintainability_lens.schemas import Characteristic, Evidence, Finding, Verdict

TESTABILITY = Characteristic.TESTABILITY


def rater_verdicts(table: dict[str, list[str]]) -> list[RaterVerdict]:
    return [
        RaterVerdict(rater=rater, file_id=file_id, characteristic=TESTABILITY, verdict=verdict)
        for file_id, verdicts in table.items()
        for rater, verdict in zip(["rater-a", "rater-b", "rater-c"], verdicts, strict=True)
    ]


def recorded(file_id: str, verdict: str, repetition: int = 0) -> RecordedFileFindings:
    evidence = [] if verdict == "unknown" else [Evidence(file="app.py", line_start=1)]
    finding = Finding(
        characteristic=TESTABILITY, verdict=Verdict(verdict), evidence=evidence, rationale="r"
    )
    return RecordedFileFindings(
        findings=[finding],
        file_id=file_id,
        approach=Approach.SIZE_ONLY,
        repetition=repetition,
        cost_usd=0.5,
    )


RATERS = rater_verdicts(
    {
        "F01": ["pass", "pass", "fail"],
        "F02": ["fail", "fail", "fail"],
        "F03": ["pass", "fail", "unknown"],
    }
)


def test_accuracy_counts_only_pairs_with_a_consensus() -> None:
    findings = [recorded("F01", "pass"), recorded("F02", "pass"), recorded("F03", "pass")]

    scores = score_evaluation(RATERS, {Approach.SIZE_ONLY: findings})

    approach = scores.approaches[0]
    assert approach.accuracy_per_characteristic[TESTABILITY] == 0.5
    assert approach.compared_pairs == 2
    assert (scores.consensus_pairs, scores.no_consensus_pairs) == (2, 1)


def test_accuracy_is_averaged_over_repetitions() -> None:
    findings = [
        recorded("F01", "pass", 0),
        recorded("F02", "fail", 0),
        recorded("F01", "pass", 1),
        recorded("F02", "pass", 1),
    ]

    approach = score_evaluation(RATERS, {Approach.SIZE_ONLY: findings}).approaches[0]

    assert approach.accuracy_overall == 0.75
    assert approach.repetitions == 2


def test_stability_is_the_share_of_pairs_with_one_verdict_in_every_repetition() -> None:
    findings = [
        recorded("F01", "pass", 0),
        recorded("F02", "fail", 0),
        recorded("F01", "pass", 1),
        recorded("F02", "pass", 1),
    ]

    approach = score_evaluation(RATERS, {Approach.SIZE_ONLY: findings}).approaches[0]

    assert approach.unanimous_share == 0.5


def test_one_repetition_has_no_stability() -> None:
    approach = score_evaluation(RATERS, {Approach.SIZE_ONLY: [recorded("F01", "pass")]}).approaches[
        0
    ]

    assert approach.unanimous_share is None


def test_each_rater_is_scored_against_the_consensus_of_the_others() -> None:
    scores = score_evaluation(RATERS, {})

    accuracy = {rater.rater: rater.accuracy_against_others for rater in scores.raters}
    assert accuracy["rater-c"] == 0.5
    assert accuracy["rater-a"] == 1.0


def test_leniency_compares_pass_shares() -> None:
    findings = [recorded("F01", "pass"), recorded("F02", "pass"), recorded("F03", "fail")]

    scores = score_evaluation(RATERS, {Approach.SIZE_ONLY: findings})

    assert scores.rater_pass_share == pytest.approx(3 / 9)
    assert scores.approaches[0].pass_share == pytest.approx(2 / 3)


def test_cost_is_summed_over_every_recorded_file() -> None:
    findings = [recorded("F01", "pass", 0), recorded("F01", "pass", 1)]

    approach = score_evaluation(RATERS, {Approach.SIZE_ONLY: findings}).approaches[0]

    assert approach.total_cost_usd == 1.0
