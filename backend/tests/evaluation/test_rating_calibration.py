from fractions import Fraction

import pytest

from maintainability_lens.evaluation import calibrate_rating_limits, derive_band_limits
from maintainability_lens.schemas import Rating

SYSTEM_COUNT = 20


def test_ordered_systems_split_at_five_thirty_five_sixty_five_and_ninety_five_percent() -> None:
    system_shares = [(Fraction(index),) * 3 for index in range(1, SYSTEM_COUNT + 1)]

    limits = calibrate_rating_limits(system_shares)

    assert limits == (
        (Rating.PLUS_PLUS, (Fraction(1),) * 3),
        (Rating.PLUS, (Fraction(7),) * 3),
        (Rating.NEUTRAL, (Fraction(13),) * 3),
        (Rating.MINUS, (Fraction(19),) * 3),
    )


def test_limits_rise_until_enough_systems_are_within_every_band_at_once() -> None:
    system_shares = [
        (Fraction(50), Fraction(20 + index), Fraction(21 - index))
        for index in range(1, SYSTEM_COUNT + 1)
    ]

    limits = dict(calibrate_rating_limits(system_shares))

    assert limits[Rating.PLUS_PLUS] == (Fraction(50), Fraction(31), Fraction(11))
    assert limits[Rating.PLUS] == (Fraction(50), Fraction(34), Fraction(14))


def test_limits_are_rounded_up_to_a_tenth_of_a_percent() -> None:
    system_shares = [(Fraction(index, 3),) * 3 for index in range(1, SYSTEM_COUNT + 1)]

    limits = dict(calibrate_rating_limits(system_shares))

    assert limits[Rating.PLUS_PLUS] == (Fraction("0.4"),) * 3


def test_calibration_without_systems_is_rejected() -> None:
    with pytest.raises(ValueError, match="no systems"):
        calibrate_rating_limits([])


def test_band_limits_are_where_seventy_eighty_and_ninety_percent_of_the_code_lies_below() -> None:
    small_system = {0: 60, 5: 20, 6: 20}
    large_system = {1: 700, 3: 100, 4: 100, 9: 100}

    assert derive_band_limits([small_system, large_system]) == (3, 5, 6)


def test_band_derivation_without_systems_is_rejected() -> None:
    with pytest.raises(ValueError, match="no systems"):
        derive_band_limits([])
