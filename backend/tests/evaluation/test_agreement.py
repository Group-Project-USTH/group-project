import pytest

from maintainability_lens.evaluation.agreement import find_consensus, krippendorff_alpha

KRIPPENDORFF_2011_UNITS = [
    [1, 1, 1],
    [2, 2, 3, 2],
    [3, 3, 3, 3],
    [3, 3, 3, 3],
    [2, 2, 2, 2],
    [1, 2, 3, 4],
    [4, 4, 4, 4],
    [1, 1, 2, 1],
    [2, 2, 2, 2],
    [5, 5, 5],
    [1, 1],
    [3],
]


def test_alpha_matches_krippendorffs_worked_nominal_example() -> None:
    assert krippendorff_alpha(KRIPPENDORFF_2011_UNITS) == pytest.approx(0.743, abs=0.0005)


def test_alpha_is_one_when_everyone_agrees() -> None:
    assert krippendorff_alpha([["pass", "pass"], ["fail", "fail", "fail"]]) == 1.0


def test_alpha_is_none_when_only_one_value_is_ever_given() -> None:
    assert krippendorff_alpha([["pass", "pass"], ["pass", "pass"]]) is None


def test_consensus_is_the_strict_majority() -> None:
    assert find_consensus(["pass", "pass", "fail"], minimum_raters=3) == "pass"


def test_a_tie_has_no_consensus() -> None:
    assert find_consensus(["pass", "pass", "fail", "fail"], minimum_raters=3) is None


def test_too_few_raters_have_no_consensus() -> None:
    assert find_consensus(["pass", "pass"], minimum_raters=3) is None
