import math

from maintainability_lens.schemas import (
    Characteristic,
    CharacteristicRating,
    Rating,
    SystemProperty,
    SystemPropertyRating,
)

# SIG/TÜV NORD CERT, Evaluation Criteria Trusted Product Maintainability V18.0 (2026-03-31),
# section 4: the System properties linked to each ISO/IEC 25010 Characteristic.
SYSTEM_PROPERTIES_PER_CHARACTERISTIC: dict[Characteristic, tuple[SystemProperty, ...]] = {
    Characteristic.MODULARITY: (
        SystemProperty.MODULE_COUPLING,
        SystemProperty.COMPONENT_ENTANGLEMENT,
        SystemProperty.COMPONENT_INDEPENDENCE,
    ),
    Characteristic.REUSABILITY: (SystemProperty.UNIT_SIZE, SystemProperty.UNIT_INTERFACING),
    Characteristic.ANALYSABILITY: (SystemProperty.DUPLICATION, SystemProperty.UNIT_SIZE),
    Characteristic.MODIFIABILITY: (
        SystemProperty.DUPLICATION,
        SystemProperty.UNIT_COMPLEXITY,
        SystemProperty.MODULE_COUPLING,
    ),
    Characteristic.TESTABILITY: (
        SystemProperty.UNIT_COMPLEXITY,
        SystemProperty.COMPONENT_INDEPENDENCE,
    ),
}
RATING_VALUES = {
    Rating.PLUS_PLUS: 2,
    Rating.PLUS: 1,
    Rating.NEUTRAL: 0,
    Rating.MINUS: -1,
    Rating.MINUS_MINUS: -2,
}
RATINGS_BY_VALUE = {value: rating for rating, value in RATING_VALUES.items()}


def average_rating(ratings: list[Rating]) -> Rating:
    average = sum(RATING_VALUES[rating] for rating in ratings) / len(ratings)
    # Half rounds up: Heitlager, Kuipers and Visser 2007, Fig. 5 shows avg(--, -) as -.
    return RATINGS_BY_VALUE[math.floor(average + 0.5)]


def rate_characteristic(
    characteristic: Characteristic, ratings: dict[SystemProperty, Rating]
) -> CharacteristicRating:
    linked = SYSTEM_PROPERTIES_PER_CHARACTERISTIC[characteristic]
    rated_from = [system_property for system_property in linked if system_property in ratings]
    missing = [system_property for system_property in linked if system_property not in ratings]
    return CharacteristicRating(
        characteristic=characteristic,
        rating=average_rating([ratings[system_property] for system_property in rated_from])
        if rated_from
        else None,
        is_partial=bool(rated_from and missing),
        rated_from=rated_from,
        missing=missing,
    )


def rate_characteristics(
    system_property_ratings: list[SystemPropertyRating],
) -> list[CharacteristicRating]:
    ratings = {
        entry.system_property: entry.rating
        for entry in system_property_ratings
        if entry.rating is not None
    }
    return [rate_characteristic(characteristic, ratings) for characteristic in Characteristic]
