"""Confusion-matrix counting for verdicts vs. ground truth.

Convention: FAIL is the positive class.

| verdict \\ truth | has problem | no problem |
|-----------------|-------------|------------|
| FAIL            | TP          | FP (false fail) |
| PASS            | FN (false pass) | TN     |
| UNKNOWN         | counted separately as `unknown` |
"""

from collections.abc import Iterable
from dataclasses import dataclass

from maintain_eval.schemas import Verdict


@dataclass(frozen=True, slots=True)
class ConfusionCounts:
    tp: int = 0
    fp: int = 0
    fn: int = 0
    tn: int = 0
    unknown: int = 0

    @property
    def decided(self) -> int:
        """Verdicts that were PASS or FAIL."""
        return self.tp + self.fp + self.fn + self.tn

    @property
    def total(self) -> int:
        return self.decided + self.unknown


def count_confusion(pairs: Iterable[tuple[Verdict, bool]]) -> ConfusionCounts:
    """Count `(verdict, ground_truth_has_problem)` pairs into TP/FP/FN/TN + unknown."""
    tp = fp = fn = tn = unknown = 0
    for verdict, has_problem in pairs:
        match verdict:
            case Verdict.UNKNOWN:
                unknown += 1
            case Verdict.FAIL if has_problem:
                tp += 1
            case Verdict.FAIL:
                fp += 1
            case Verdict.PASS if has_problem:
                fn += 1
            case Verdict.PASS:
                tn += 1
    return ConfusionCounts(tp=tp, fp=fp, fn=fn, tn=tn, unknown=unknown)
