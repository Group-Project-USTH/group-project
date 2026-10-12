import pytest

from maintain_eval.evaluation import ConfusionCounts, count_confusion
from maintain_eval.schemas import Verdict


def test_empty_input_is_all_zero() -> None:
    counts = count_confusion([])
    assert counts == ConfusionCounts()
    assert counts.total == 0


@pytest.mark.parametrize(
    ("verdict", "has_problem", "expected"),
    [
        (Verdict.FAIL, True, ConfusionCounts(tp=1)),
        (Verdict.FAIL, False, ConfusionCounts(fp=1)),
        (Verdict.PASS, True, ConfusionCounts(fn=1)),
        (Verdict.PASS, False, ConfusionCounts(tn=1)),
        (Verdict.UNKNOWN, True, ConfusionCounts(unknown=1)),
        (Verdict.UNKNOWN, False, ConfusionCounts(unknown=1)),
    ],
    ids=["TP", "FP-false-fail", "FN-false-pass", "TN", "unknown-problem", "unknown-clean"],
)
def test_each_cell(verdict: Verdict, has_problem: bool, expected: ConfusionCounts) -> None:
    assert count_confusion([(verdict, has_problem)]) == expected


def test_mixed_input_and_totals() -> None:
    pairs = [
        (Verdict.FAIL, True),
        (Verdict.FAIL, True),
        (Verdict.FAIL, False),
        (Verdict.PASS, True),
        (Verdict.PASS, False),
        (Verdict.PASS, False),
        (Verdict.PASS, False),
        (Verdict.UNKNOWN, True),
        (Verdict.UNKNOWN, False),
    ]
    counts = count_confusion(pairs)
    assert counts == ConfusionCounts(tp=2, fp=1, fn=1, tn=3, unknown=2)
    assert counts.decided == 7
    assert counts.total == len(pairs)


def test_accepts_any_iterable() -> None:
    gen = ((Verdict.FAIL, True) for _ in range(3))
    assert count_confusion(gen).tp == 3
