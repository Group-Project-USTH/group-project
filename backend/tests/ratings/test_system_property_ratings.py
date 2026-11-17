import pytest

from maintainability_lens.ratings import rate_system_properties
from maintainability_lens.schemas import (
    Measure,
    MeasureName,
    ProjectMeasures,
    Rating,
    SystemProperty,
    SystemPropertyRating,
)

COMPLEXITY_PER_BAND = {"low": 1, "moderate": 15, "high": 30, "very_high": 60}
SIZE_PER_BAND = {"low": 10, "moderate": 20, "high": 40, "very_high": 80}


def unit(
    lines_of_code: int,
    cyclomatic_complexity: int = 1,
    parameter_count: int = 0,
    is_test_code: bool = False,
    index: int = 0,
) -> list[Measure]:
    location = {
        "function": f"f{index}",
        "file": "test_app.py" if is_test_code else "app.py",
        "line_start": index + 1,
        "line_end": index + 1,
        "is_test_code": is_test_code,
    }
    return [
        Measure(name=MeasureName.FUNCTION_LINES_OF_CODE, value=lines_of_code, **location),
        Measure(name=MeasureName.CYCLOMATIC_COMPLEXITY, value=cyclomatic_complexity, **location),
        Measure(name=MeasureName.PARAMETER_COUNT, value=parameter_count, **location),
    ]


def a_file(
    lines_of_code: int, duplicated_lines: int = 0, fan_in: int = 0, is_test_code: bool = False
) -> list[Measure]:
    location = {
        "file": "test_app.py" if is_test_code else "app.py",
        "line_start": 1,
        "line_end": 1,
        "is_test_code": is_test_code,
    }
    return [
        Measure(name=MeasureName.FILE_LINES_OF_CODE, value=lines_of_code, **location),
        Measure(name=MeasureName.DUPLICATED_LINES, value=duplicated_lines, **location),
        Measure(name=MeasureName.FILE_FAN_IN, value=fan_in, **location),
    ]


def units_with_complexity_lines(moderate: int, high: int, very_high: int) -> list[Measure]:
    lines_per_band = {
        "low": 100 - moderate - high - very_high,
        "moderate": moderate,
        "high": high,
        "very_high": very_high,
    }
    return [
        measure
        for index, (band, lines) in enumerate(lines_per_band.items())
        if lines
        for measure in unit(lines, COMPLEXITY_PER_BAND[band], index=index)
    ]


def rating_of(measures: list[Measure], system_property: SystemProperty) -> SystemPropertyRating:
    ratings = rate_system_properties(ProjectMeasures(measures=measures))
    return next(rating for rating in ratings if rating.system_property is system_property)


@pytest.mark.parametrize(
    ("moderate", "high", "very_high", "expected"),
    [
        pytest.param(25, 0, 0, Rating.PLUS_PLUS, id="25-0-0-is-++"),
        pytest.param(26, 0, 0, Rating.PLUS, id="26-0-0-is-+"),
        pytest.param(30, 5, 0, Rating.PLUS, id="30-5-0-is-+"),
        pytest.param(30, 6, 0, Rating.NEUTRAL, id="30-6-0-is-o"),
        pytest.param(40, 10, 0, Rating.NEUTRAL, id="40-10-0-is-o"),
        pytest.param(40, 10, 1, Rating.MINUS, id="40-10-1-is--"),
        pytest.param(50, 15, 5, Rating.MINUS, id="50-15-5-is--"),
        pytest.param(51, 0, 0, Rating.MINUS_MINUS, id="51-0-0-is---"),
        pytest.param(0, 0, 6, Rating.MINUS_MINUS, id="0-0-6-is---"),
    ],
)
def test_unit_complexity_is_rated_with_the_2007_table_per_band(
    moderate: int, high: int, very_high: int, expected: Rating
) -> None:
    measures = units_with_complexity_lines(moderate, high, very_high)

    assert rating_of(measures, SystemProperty.UNIT_COMPLEXITY).rating is expected


@pytest.mark.parametrize(
    ("duplicated_lines", "expected"),
    [
        pytest.param(30, Rating.PLUS_PLUS, id="3.0%-is-++"),
        pytest.param(31, Rating.PLUS, id="3.1%-is-+"),
        pytest.param(50, Rating.PLUS, id="5.0%-is-+"),
        pytest.param(100, Rating.NEUTRAL, id="10%-is-o"),
        pytest.param(200, Rating.MINUS, id="20%-is--"),
        pytest.param(201, Rating.MINUS_MINUS, id="20.1%-is---"),
    ],
)
def test_duplication_is_rated_with_the_2007_table(duplicated_lines: int, expected: Rating) -> None:
    measures = a_file(lines_of_code=1000, duplicated_lines=duplicated_lines)

    assert rating_of(measures, SystemProperty.DUPLICATION).rating is expected


def test_duplicated_test_code_does_not_count_against_duplication() -> None:
    measures = [
        *a_file(lines_of_code=1000, duplicated_lines=0),
        *a_file(lines_of_code=1000, duplicated_lines=900, is_test_code=True),
    ]

    assert rating_of(measures, SystemProperty.DUPLICATION).rating is Rating.PLUS_PLUS


def units_with_size_lines(low: int, moderate: int, high: int, very_high: int) -> list[Measure]:
    lines_per_band = {"low": low, "moderate": moderate, "high": high, "very_high": very_high}
    return [
        measure
        for index, (band, lines) in enumerate(lines_per_band.items())
        for copy in range(lines // SIZE_PER_BAND[band])
        for measure in unit(SIZE_PER_BAND[band], index=index * 1000 + copy)
    ]


@pytest.mark.parametrize(
    ("low", "moderate", "high", "very_high", "meets_limit"),
    [
        pytest.param(520, 240, 160, 80, True, id="48-24-8-meets"),
        pytest.param(500, 260, 160, 80, False, id="50%-moderate-or-worse-fails"),
        pytest.param(520, 240, 80, 160, False, id="16%-very-high-fails"),
    ],
)
def test_unit_size_has_no_rating_but_is_checked_against_the_four_star_limit(
    low: int, moderate: int, high: int, very_high: int, meets_limit: bool
) -> None:
    measures = units_with_size_lines(low, moderate, high, very_high)

    unit_size = rating_of(measures, SystemProperty.UNIT_SIZE)

    assert unit_size.rating is None
    assert unit_size.meets_four_star_limit is meets_limit


def test_unit_interfacing_under_every_four_star_limit_meets_it() -> None:
    measures = [
        *unit(1000, parameter_count=0, index=0),
        *unit(120, parameter_count=3, index=1),
        *unit(25, parameter_count=5, index=2),
        *unit(9, parameter_count=7, index=3),
    ]

    assert rating_of(measures, SystemProperty.UNIT_INTERFACING).meets_four_star_limit is True


def test_a_share_exactly_at_the_four_star_limit_meets_it() -> None:
    measures = [*unit(991, index=0), *unit(9, parameter_count=7, index=1)]

    assert rating_of(measures, SystemProperty.UNIT_INTERFACING).meets_four_star_limit is True


def test_a_share_just_over_the_four_star_limit_fails_it() -> None:
    measures = [*unit(990, index=0), *unit(10, parameter_count=7, index=1)]

    assert rating_of(measures, SystemProperty.UNIT_INTERFACING).meets_four_star_limit is False


def test_module_coupling_is_checked_against_the_four_star_limit() -> None:
    hub = a_file(lines_of_code=20, fan_in=60)
    rest = [measure.model_copy(update={"file": "rest.py"}) for measure in a_file(lines_of_code=980)]

    module_coupling = rating_of([*hub, *rest], SystemProperty.MODULE_COUPLING)

    assert module_coupling.rating is None
    assert module_coupling.meets_four_star_limit is False


def test_a_project_without_production_code_has_nothing_rated() -> None:
    ratings = rate_system_properties(ProjectMeasures(measures=[]))

    assert {(rating.rating, rating.meets_four_star_limit) for rating in ratings} == {(None, None)}


def test_every_rating_names_the_source_of_its_thresholds() -> None:
    ratings = rate_system_properties(ProjectMeasures(measures=a_file(lines_of_code=10)))

    assert {rating.system_property: rating.threshold_source for rating in ratings} == {
        SystemProperty.UNIT_COMPLEXITY: "Heitlager, Kuipers and Visser 2007",
        SystemProperty.DUPLICATION: "Heitlager, Kuipers and Visser 2007",
        SystemProperty.UNIT_SIZE: "SIG/TÜV NORD Guidance for Producers V18.1 (2026), 4-star limit",
        SystemProperty.UNIT_INTERFACING: (
            "SIG/TÜV NORD Guidance for Producers V18.1 (2026), 4-star limit"
        ),
        SystemProperty.MODULE_COUPLING: (
            "SIG/TÜV NORD Guidance for Producers V18.1 (2026), 4-star limit"
        ),
    }
