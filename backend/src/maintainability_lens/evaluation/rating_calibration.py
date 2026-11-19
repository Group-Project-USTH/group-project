import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from fractions import Fraction

from maintainability_lens.ratings import BandLimits, BandShares
from maintainability_lens.schemas import Rating

# SIG/TÜV NORD Evaluation Criteria Trusted Product Maintainability V18.0 (2026), section 5,
# p. 11: benchmark systems fall 5/30/30/30/5 % into 5...1 stars, so these are the shares of
# systems rated at least each Rating.
SYSTEM_PERCENTAGE_AT_LEAST: tuple[tuple[Rating, int], ...] = (
    (Rating.PLUS_PLUS, 5),
    (Rating.PLUS, 35),
    (Rating.NEUTRAL, 65),
    (Rating.MINUS, 95),
)
LIMIT_STEP_PERCENTAGE = Fraction(1, 10)
# Alves, Ypma and Visser, "Deriving Metric Thresholds from Benchmark Data", ICSM 2010,
# section IV: the low, moderate and high bands end where 70, 80 and 90 % of the
# benchmark's code lies at or below the Measure, each system weighing the same.
BAND_LIMIT_QUANTILES = (Fraction(70, 100), Fraction(80, 100), Fraction(90, 100))


def round_up_to_step(share: Fraction) -> Fraction:
    return math.ceil(share / LIMIT_STEP_PERCENTAGE) * LIMIT_STEP_PERCENTAGE


def is_within(shares: BandShares, limits: BandShares) -> bool:
    return all(share <= limit for share, limit in zip(shares, limits, strict=True))


def find_limits(
    system_shares: Sequence[BandShares], sorted_columns: list[list[Fraction]], percentage: int
) -> BandShares:
    system_count = len(system_shares)
    target_count = Fraction(percentage * system_count, 100)
    for rank in range(math.ceil(target_count), system_count + 1):
        moderate, high, very_high = (
            round_up_to_step(column[rank - 1]) for column in sorted_columns
        )
        limits = (moderate, high, very_high)
        if sum(is_within(shares, limits) for shares in system_shares) >= target_count:
            return limits
    raise AssertionError("every system is within the highest shares")


def calibrate_rating_limits(
    system_shares: Sequence[BandShares],
) -> tuple[tuple[Rating, BandShares], ...]:
    if not system_shares:
        raise ValueError("no systems to calibrate on")
    sorted_columns = [sorted(column) for column in zip(*system_shares, strict=True)]
    return tuple(
        (rating, find_limits(system_shares, sorted_columns, percentage))
        for rating, percentage in SYSTEM_PERCENTAGE_AT_LEAST
    )


def derive_band_limits(
    lines_of_code_per_value_per_system: Sequence[Mapping[int, int]],
) -> BandLimits:
    if not lines_of_code_per_value_per_system:
        raise ValueError("no systems to derive band limits from")
    weight_per_value: defaultdict[int, Fraction] = defaultdict(Fraction)
    system_count = len(lines_of_code_per_value_per_system)
    for lines_of_code_per_value in lines_of_code_per_value_per_system:
        system_lines_of_code = sum(lines_of_code_per_value.values())
        for value, lines in lines_of_code_per_value.items():
            weight_per_value[value] += Fraction(lines, system_lines_of_code * system_count)
    cumulative_weight = Fraction(0)
    cumulative_weights = []
    for value in sorted(weight_per_value):
        cumulative_weight += weight_per_value[value]
        cumulative_weights.append((value, cumulative_weight))
    low, moderate, high = (
        next(value for value, weight in cumulative_weights if weight >= quantile)
        for quantile in BAND_LIMIT_QUANTILES
    )
    return low, moderate, high
