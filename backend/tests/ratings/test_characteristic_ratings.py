from maintainability_lens.ratings import rate_characteristics
from maintainability_lens.schemas import (
    Characteristic,
    CharacteristicRating,
    Rating,
    SystemProperty,
    SystemPropertyRating,
)


def rated(system_property: SystemProperty, rating: Rating | None) -> SystemPropertyRating:
    return SystemPropertyRating(
        system_property=system_property, rating=rating, threshold_source="test"
    )


def characteristic_rating(
    ratings: list[SystemPropertyRating], characteristic: Characteristic
) -> CharacteristicRating:
    return next(
        entry for entry in rate_characteristics(ratings) if entry.characteristic is characteristic
    )


def test_a_characteristic_with_one_of_two_system_properties_rated_is_partial() -> None:
    ratings = [rated(SystemProperty.DUPLICATION, Rating.PLUS_PLUS)]

    analysability = characteristic_rating(ratings, Characteristic.ANALYSABILITY)

    assert analysability == CharacteristicRating(
        characteristic=Characteristic.ANALYSABILITY,
        rating=Rating.PLUS_PLUS,
        is_partial=True,
        rated_from=[SystemProperty.DUPLICATION],
        missing=[SystemProperty.UNIT_SIZE],
    )


def test_the_rated_system_properties_are_averaged_and_a_half_rounds_up() -> None:
    ratings = [
        rated(SystemProperty.DUPLICATION, Rating.MINUS_MINUS),
        rated(SystemProperty.UNIT_COMPLEXITY, Rating.MINUS),
    ]

    modifiability = characteristic_rating(ratings, Characteristic.MODIFIABILITY)

    assert modifiability.rating is Rating.MINUS
    assert modifiability.missing == [SystemProperty.MODULE_COUPLING]


def test_a_positive_half_also_rounds_up() -> None:
    ratings = [
        rated(SystemProperty.DUPLICATION, Rating.PLUS),
        rated(SystemProperty.UNIT_COMPLEXITY, Rating.NEUTRAL),
    ]

    assert characteristic_rating(ratings, Characteristic.MODIFIABILITY).rating is Rating.PLUS


def test_a_characteristic_with_nothing_rated_has_no_rating() -> None:
    ratings = [
        rated(SystemProperty.UNIT_COMPLEXITY, Rating.PLUS),
        rated(SystemProperty.MODULE_COUPLING, None),
    ]

    modularity = characteristic_rating(ratings, Characteristic.MODULARITY)

    assert modularity == CharacteristicRating(
        characteristic=Characteristic.MODULARITY,
        rating=None,
        is_partial=False,
        rated_from=[],
        missing=[
            SystemProperty.MODULE_COUPLING,
            SystemProperty.COMPONENT_ENTANGLEMENT,
            SystemProperty.COMPONENT_INDEPENDENCE,
        ],
    )


def test_testability_follows_unit_complexity_while_components_are_not_modelled() -> None:
    ratings = [rated(SystemProperty.UNIT_COMPLEXITY, Rating.MINUS)]

    testability = characteristic_rating(ratings, Characteristic.TESTABILITY)

    assert (testability.rating, testability.missing) == (
        Rating.MINUS,
        [SystemProperty.COMPONENT_INDEPENDENCE],
    )


def test_every_characteristic_is_rated_in_glossary_order() -> None:
    assert [entry.characteristic for entry in rate_characteristics([])] == list(Characteristic)
