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
GUIDANCE_V18_1_FOUR_STAR = "SIG/TÜV NORD Guidance for Producers V18.1 (2026), 4-star limit"

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
# SIG/TÜV NORD Guidance for Producers V18.1 (2026-03-31), section 3: the most LOC (%) in
# the moderate-or-worse, high-or-worse and very high bands for 4 stars (cumulative).
FOUR_STAR_LIMITS: dict[SystemProperty, BandShares] = {
    SystemProperty.UNIT_SIZE: (Fraction("48.0"), Fraction("24.2"), Fraction("9.1")),
    SystemProperty.UNIT_INTERFACING: (Fraction("15.4"), Fraction("3.4"), Fraction("0.9")),
    SystemProperty.MODULE_COUPLING: (Fraction("9.7"), Fraction("5.3"), Fraction("1.8")),
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


def rate_duplication(project_measures: ProjectMeasures) -> SystemPropertyRating:
    def production_total(name: MeasureName) -> int:
        return sum(
            measure.value
            for measure in project_measures.measures
            if measure.name is name and not measure.is_test_code
        )

    lines_of_code = production_total(MeasureName.FILE_LINES_OF_CODE)
    rating = None
    if lines_of_code:
        duplicated = percentage(production_total(MeasureName.DUPLICATED_LINES), lines_of_code)
        rating = next(
            (rating for rating, limit in DUPLICATION_RATING_LIMITS if duplicated <= limit),
            Rating.MINUS_MINUS,
        )
    return SystemPropertyRating(
        system_property=SystemProperty.DUPLICATION, rating=rating, threshold_source=HEITLAGER_2007
    )


def check_four_star_limit(profile: RiskProfile) -> SystemPropertyRating:
    shares = band_shares(profile)
    return SystemPropertyRating(
        system_property=profile.system_property,
        meets_four_star_limit=(
            None
            if shares is None
            else is_within(cumulative(shares), FOUR_STAR_LIMITS[profile.system_property])
        ),
        threshold_source=GUIDANCE_V18_1_FOUR_STAR,
    )


def rate_system_properties(project_measures: ProjectMeasures) -> list[SystemPropertyRating]:
    profiles = {
        profile.system_property: profile for profile in build_risk_profiles(project_measures)
    }
    return [
        rate_unit_complexity(profiles[SystemProperty.UNIT_COMPLEXITY]),
        rate_duplication(project_measures),
        *(check_four_star_limit(profiles[system_property]) for system_property in FOUR_STAR_LIMITS),
    ]
