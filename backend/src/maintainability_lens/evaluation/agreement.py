from collections import Counter, defaultdict
from collections.abc import Hashable, Sequence
from itertools import permutations


def krippendorff_alpha(units: Sequence[Sequence[Hashable]]) -> float | None:
    coincidences: defaultdict[tuple[Hashable, Hashable], float] = defaultdict(float)
    for values in units:
        if len(values) < 2:
            continue
        for first, second in permutations(values, 2):
            coincidences[(first, second)] += 1 / (len(values) - 1)
    totals: defaultdict[Hashable, float] = defaultdict(float)
    for (first, _), weight in coincidences.items():
        totals[first] += weight
    pairable_values = sum(totals.values())
    observed_disagreement = sum(
        weight for (first, second), weight in coincidences.items() if first != second
    )
    expected_disagreement = sum(
        totals[first] * totals[second] for first in totals for second in totals if first != second
    )
    if expected_disagreement == 0:
        return None
    return 1 - (pairable_values - 1) * observed_disagreement / expected_disagreement


def find_consensus[Value: Hashable](values: Sequence[Value], minimum_raters: int) -> Value | None:
    if len(values) < minimum_raters:
        return None
    value, count = Counter(values).most_common(1)[0]
    return value if count * 2 > len(values) else None
