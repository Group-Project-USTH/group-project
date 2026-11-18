from collections import defaultdict
from statistics import mean

from pydantic import BaseModel

from maintainability_lens.evaluation.agreement import find_consensus, krippendorff_alpha
from maintainability_lens.evaluation.rater_verdicts import RaterVerdict
from maintainability_lens.evaluation.recorded_findings import Approach, RecordedFileFindings
from maintainability_lens.schemas import Characteristic, Verdict

Pair = tuple[str, Characteristic]

# Why: fixed in docs/evaluation/rating-protocol.md before any Verdict was given.
MINIMUM_RATERS_FOR_CONSENSUS = 3
# Why: with three Raters, leaving one out leaves two, who must then agree.
MINIMUM_OTHER_RATERS_FOR_CONSENSUS = 2


class RaterScores(BaseModel):
    rater: str
    accuracy_against_others: float | None


class ApproachScores(BaseModel):
    approach: Approach
    models: list[str]
    repetitions: int
    compared_pairs: int
    accuracy_overall: float | None
    accuracy_per_characteristic: dict[Characteristic, float | None]
    pass_share: float | None
    unanimous_share: float | None
    alpha_across_repetitions: float | None
    total_cost_usd: float | None


class EvaluationScores(BaseModel):
    rater_count: int
    consensus_pairs: int
    no_consensus_pairs: int
    alpha_overall: float | None
    alpha_per_characteristic: dict[Characteristic, float | None]
    rater_pass_share: float | None
    raters: list[RaterScores]
    approaches: list[ApproachScores]


def share(matches: list[bool]) -> float | None:
    return sum(matches) / len(matches) if matches else None


def group_rater_verdicts(rater_verdicts: list[RaterVerdict]) -> dict[Pair, dict[str, Verdict]]:
    grouped: dict[Pair, dict[str, Verdict]] = defaultdict(dict)
    for entry in rater_verdicts:
        grouped[(entry.file_id, entry.characteristic)][entry.rater] = entry.verdict
    return grouped


def group_findings(recorded: list[RecordedFileFindings]) -> dict[int, dict[Pair, Verdict]]:
    grouped: dict[int, dict[Pair, Verdict]] = defaultdict(dict)
    for entry in recorded:
        for finding in entry.findings:
            grouped[entry.repetition][(entry.file_id, finding.characteristic)] = finding.verdict
    return grouped


def mean_accuracy(
    verdicts_per_repetition: dict[int, dict[Pair, Verdict]],
    consensus: dict[Pair, Verdict],
    characteristic: Characteristic | None,
) -> float | None:
    accuracies = []
    for verdicts in verdicts_per_repetition.values():
        accuracy = share(
            [
                verdict is consensus[pair]
                for pair, verdict in verdicts.items()
                if pair in consensus and characteristic in (None, pair[1])
            ]
        )
        if accuracy is not None:
            accuracies.append(accuracy)
    return mean(accuracies) if accuracies else None


def score_approach(
    approach: Approach, recorded: list[RecordedFileFindings], consensus: dict[Pair, Verdict]
) -> ApproachScores:
    verdicts_per_repetition = group_findings(recorded)
    verdicts_per_pair: dict[Pair, list[Verdict]] = defaultdict(list)
    for verdicts in verdicts_per_repetition.values():
        for pair, verdict in verdicts.items():
            verdicts_per_pair[pair].append(verdict)
    repeated = [verdicts for verdicts in verdicts_per_pair.values() if len(verdicts) > 1]
    costs = [entry.cost_usd for entry in recorded if entry.cost_usd is not None]
    return ApproachScores(
        approach=approach,
        models=sorted({entry.model for entry in recorded if entry.model}),
        repetitions=len(verdicts_per_repetition),
        compared_pairs=len(set(verdicts_per_pair) & set(consensus)),
        accuracy_overall=mean_accuracy(verdicts_per_repetition, consensus, None),
        accuracy_per_characteristic={
            characteristic: mean_accuracy(verdicts_per_repetition, consensus, characteristic)
            for characteristic in Characteristic
        },
        pass_share=share(
            [
                verdict is Verdict.PASS
                for verdicts in verdicts_per_pair.values()
                for verdict in verdicts
            ]
        ),
        unanimous_share=share([len(set(verdicts)) == 1 for verdicts in repeated]),
        alpha_across_repetitions=krippendorff_alpha(repeated) if repeated else None,
        total_cost_usd=sum(costs) if costs else None,
    )


def score_rater(rater: str, verdicts_per_pair: dict[Pair, dict[str, Verdict]]) -> RaterScores:
    matches = []
    for verdicts in verdicts_per_pair.values():
        if rater not in verdicts:
            continue
        others = [verdict for other, verdict in verdicts.items() if other != rater]
        consensus = find_consensus(others, MINIMUM_OTHER_RATERS_FOR_CONSENSUS)
        if consensus is not None:
            matches.append(verdicts[rater] is consensus)
    return RaterScores(rater=rater, accuracy_against_others=share(matches))


def score_evaluation(
    rater_verdicts: list[RaterVerdict],
    recorded_per_approach: dict[Approach, list[RecordedFileFindings]],
) -> EvaluationScores:
    verdicts_per_pair = group_rater_verdicts(rater_verdicts)
    consensus = {
        pair: verdict
        for pair, verdicts in verdicts_per_pair.items()
        if (verdict := find_consensus(list(verdicts.values()), MINIMUM_RATERS_FOR_CONSENSUS))
        is not None
    }
    raters = sorted({entry.rater for entry in rater_verdicts})
    return EvaluationScores(
        rater_count=len(raters),
        consensus_pairs=len(consensus),
        no_consensus_pairs=len(verdicts_per_pair) - len(consensus),
        alpha_overall=krippendorff_alpha(
            [list(verdicts.values()) for verdicts in verdicts_per_pair.values()]
        ),
        alpha_per_characteristic={
            characteristic: krippendorff_alpha(
                [
                    list(verdicts.values())
                    for (_, pair_characteristic), verdicts in verdicts_per_pair.items()
                    if pair_characteristic is characteristic
                ]
            )
            for characteristic in Characteristic
        },
        rater_pass_share=share([entry.verdict is Verdict.PASS for entry in rater_verdicts]),
        raters=[score_rater(rater, verdicts_per_pair) for rater in raters],
        approaches=[
            score_approach(approach, recorded, consensus)
            for approach, recorded in recorded_per_approach.items()
        ],
    )
