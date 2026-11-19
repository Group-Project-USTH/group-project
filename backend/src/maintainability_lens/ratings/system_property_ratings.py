from fractions import Fraction

from maintainability_lens.ratings.risk_profiles import build_risk_profiles
from maintainability_lens.schemas import (
    MeasureName,
    ProjectMeasures,
    Rating,
    RiskBand,
    RiskProfile,
    SystemProperty,
    SystemPropertyRating,
)

HEITLAGER_2007 = "Heitlager, Kuipers and Visser 2007"
CALIBRATION = "maintainability-lens calibration on 100 Python projects (2026-11)"

BandShares = tuple[Fraction, Fraction, Fraction]

# Heitlager, Kuipers and Visser 2007, p. 6: the most LOC (%) allowed in the moderate, high
# and very high bands, each band on its own; a profile meeting none of them is rated --.
UNIT_COMPLEXITY_RATING_LIMITS: tuple[tuple[Rating, BandShares], ...] = tuple(
    (rating, (Fraction(moderate), Fraction(high), Fraction(very_high)))
    for rating, moderate, high, very_high in (
        (Rating.PLUS_PLUS, 25, 0, 0),
        (Rating.PLUS, 30, 5, 0),
        (Rating.NEUTRAL, 40, 10, 0),
        (Rating.MINUS, 50, 15, 5),
    )
)
# Heitlager, Kuipers and Visser 2007, p. 7: the most duplicated LOC (%) for each Rating.
DUPLICATION_RATING_LIMITS: tuple[tuple[Rating, Fraction], ...] = (
    (Rating.PLUS_PLUS, Fraction(3)),
    (Rating.PLUS, Fraction(5)),
    (Rating.NEUTRAL, Fraction(10)),
    (Rating.MINUS, Fraction(20)),
)
# docs/evaluation/rating-calibration.md: the most LOC (%) in the moderate-or-worse,
# high-or-worse and very high bands (cumulative) for each Rating, calibrated so that the
# 100 projects of the Calibration set fall 5/30/30/30/5 % into ++ ... --.
CALIBRATED_RATING_LIMITS: dict[SystemProperty, tuple[tuple[Rating, BandShares], ...]] = {
    system_property: tuple(
        (rating, (Fraction(moderate), Fraction(high), Fraction(very_high)))
        for rating, (moderate, high, very_high) in zip(
            (Rating.PLUS_PLUS, Rating.PLUS, Rating.NEUTRAL, Rating.MINUS), limits, strict=True
        )
    )
    for system_property, limits in {
        SystemProperty.UNIT_SIZE: (
            ("31.1", "9.3", "0.0"),
            ("54.8", "27.8", "9.3"),
            ("66.4", "43.5", "21.4"),
            ("78.7", "63.2", "37.8"),
        ),
        SystemProperty.UNIT_INTERFACING: (
            ("16.4", "2.1", "0.0"),
            ("32.0", "12.8", "6.4"),
            ("40.9", "22.7", "11.9"),
            ("62.1", "38.4", "30.7"),
        ),
        SystemProperty.MODULE_COUPLING: (
            ("0.0", "0.0", "0.0"),
            ("23.7", "16.4", "2.8"),
            ("39.0", "29.9", "15.0"),
            ("62.1", "52.1", "29.7"),
        ),
    }.items()
}


def percentage(lines: int, total: int) -> Fraction:
    return Fraction(100 * lines, total)


def band_shares(profile: RiskProfile) -> BandShares | None:
    lines = profile.lines_of_code_per_band
    total = sum(lines.values())
    if not total:
        return None
    return (
        percentage(lines[RiskBand.MODERATE], total),
        percentage(lines[RiskBand.HIGH], total),
        percentage(lines[RiskBand.VERY_HIGH], total),
    )


def cumulative(shares: BandShares) -> BandShares:
    moderate, high, very_high = shares
    return moderate + high + very_high, high + very_high, very_high


def is_within(shares: BandShares, limits: BandShares) -> bool:
    return all(share <= limit for share, limit in zip(shares, limits, strict=True))


def rate_unit_complexity(profile: RiskProfile) -> SystemPropertyRating:
    shares = band_shares(profile)
    rating = None
    if shares is not None:
        rating = next(
            (
                rating
                for rating, limits in UNIT_COMPLEXITY_RATING_LIMITS
                if is_within(shares, limits)
            ),
            Rating.MINUS_MINUS,
        )
    return SystemPropertyRating(
        system_property=SystemProperty.UNIT_COMPLEXITY,
        rating=rating,
        threshold_source=HEITLAGER_2007,
    )


def total_of(project_measures: ProjectMeasures, name: MeasureName, is_test_code: bool) -> int:
    return sum(
        measure.value
        for measure in project_measures.measures
        if measure.name is name and measure.is_test_code is is_test_code
    )


def find_duplicated_percentage(project_measures: ProjectMeasures) -> Fraction | None:
    lines_of_code = total_of(project_measures, MeasureName.FILE_LINES_OF_CODE, False)
    if not lines_of_code:
        return None
    duplicated = total_of(project_measures, MeasureName.DUPLICATED_LINES, False)
    return percentage(duplicated, lines_of_code)


def rate_duplication(project_measures: ProjectMeasures) -> SystemPropertyRating:
    duplicated = find_duplicated_percentage(project_measures)
    rating = None
    if duplicated is not None:
        rating = next(
            (rating for rating, limit in DUPLICATION_RATING_LIMITS if duplicated <= limit),
            Rating.MINUS_MINUS,
        )
    return SystemPropertyRating(
        system_property=SystemProperty.DUPLICATION, rating=rating, threshold_source=HEITLAGER_2007
    )


def find_cumulative_band_shares(profile: RiskProfile) -> BandShares | None:
    shares = band_shares(profile)
    return None if shares is None else cumulative(shares)


def rate_with_calibrated_limits(profile: RiskProfile) -> SystemPropertyRating:
    shares = find_cumulative_band_shares(profile)
    rating = None
    if shares is not None:
        rating = next(
            (
                rating
                for rating, limits in CALIBRATED_RATING_LIMITS[profile.system_property]
                if is_within(shares, limits)
            ),
            Rating.MINUS_MINUS,
        )
    return SystemPropertyRating(
        system_property=profile.system_property, rating=rating, threshold_source=CALIBRATION
    )


def rate_system_properties(project_measures: ProjectMeasures) -> list[SystemPropertyRating]:
    profiles = {
        profile.system_property: profile for profile in build_risk_profiles(project_measures)
    }
    return [
        rate_unit_complexity(profiles[SystemProperty.UNIT_COMPLEXITY]),
        rate_duplication(project_measures),
        *(
            rate_with_calibrated_limits(profiles[system_property])
            for system_property in CALIBRATED_RATING_LIMITS
        ),
    ]
