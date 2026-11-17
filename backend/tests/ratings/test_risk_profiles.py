import pytest

from maintainability_lens.ratings import build_risk_profiles
from maintainability_lens.schemas import (
    Measure,
    MeasureName,
    ProjectMeasures,
    RiskBand,
    RiskProfile,
    SystemProperty,
)


def unit_measures(
    function: str,
    lines_of_code: int,
    cyclomatic_complexity: int = 1,
    parameter_count: int = 0,
    is_test_code: bool = False,
) -> list[Measure]:
    location = {
        "function": function,
        "file": "test_app.py" if is_test_code else "app.py",
        "line_start": 1,
        "line_end": 2,
        "is_test_code": is_test_code,
    }
    return [
        Measure(name=MeasureName.FUNCTION_LINES_OF_CODE, value=lines_of_code, **location),
        Measure(name=MeasureName.CYCLOMATIC_COMPLEXITY, value=cyclomatic_complexity, **location),
        Measure(name=MeasureName.PARAMETER_COUNT, value=parameter_count, **location),
    ]


def file_measures(file: str, lines_of_code: int, fan_in: int) -> list[Measure]:
    location = {"file": file, "line_start": 1, "line_end": 1}
    return [
        Measure(name=MeasureName.FILE_LINES_OF_CODE, value=lines_of_code, **location),
        Measure(name=MeasureName.FILE_FAN_IN, value=fan_in, **location),
    ]


def profile_of(measures: list[Measure], system_property: SystemProperty) -> RiskProfile:
    profiles = build_risk_profiles(ProjectMeasures(measures=measures))
    return next(profile for profile in profiles if profile.system_property is system_property)


def test_unit_complexity_profile_is_the_share_of_unit_lines_in_each_band() -> None:
    measures = [
        *unit_measures("simple", lines_of_code=10, cyclomatic_complexity=5),
        *unit_measures("branchy", lines_of_code=20, cyclomatic_complexity=15),
        *unit_measures("complex", lines_of_code=30, cyclomatic_complexity=30),
        *unit_measures("untestable", lines_of_code=40, cyclomatic_complexity=60),
    ]

    profile = profile_of(measures, SystemProperty.UNIT_COMPLEXITY)

    assert profile.lines_of_code_per_band == {
        RiskBand.LOW: 10,
        RiskBand.MODERATE: 20,
        RiskBand.HIGH: 30,
        RiskBand.VERY_HIGH: 40,
    }
    assert profile.percentage_per_band == {
        RiskBand.LOW: 10.0,
        RiskBand.MODERATE: 20.0,
        RiskBand.HIGH: 30.0,
        RiskBand.VERY_HIGH: 40.0,
    }


def test_test_code_is_left_out_of_every_risk_profile() -> None:
    measures = [
        *unit_measures("production", lines_of_code=10, cyclomatic_complexity=1),
        *unit_measures("test_huge", lines_of_code=90, cyclomatic_complexity=99, is_test_code=True),
    ]

    profile = profile_of(measures, SystemProperty.UNIT_COMPLEXITY)

    assert profile.lines_of_code_per_band[RiskBand.LOW] == 10
    assert profile.lines_of_code_per_band[RiskBand.VERY_HIGH] == 0


@pytest.mark.parametrize(
    ("system_property", "measures", "expected_band"),
    [
        pytest.param(
            SystemProperty.UNIT_COMPLEXITY,
            unit_measures("f", 1, cyclomatic_complexity=10),
            RiskBand.LOW,
            id="complexity-10-is-low",
        ),
        pytest.param(
            SystemProperty.UNIT_COMPLEXITY,
            unit_measures("f", 1, cyclomatic_complexity=11),
            RiskBand.MODERATE,
            id="complexity-11-is-moderate",
        ),
        pytest.param(
            SystemProperty.UNIT_COMPLEXITY,
            unit_measures("f", 1, cyclomatic_complexity=51),
            RiskBand.VERY_HIGH,
            id="complexity-51-is-very-high",
        ),
        pytest.param(
            SystemProperty.UNIT_SIZE, unit_measures("f", 15), RiskBand.LOW, id="size-15-is-low"
        ),
        pytest.param(
            SystemProperty.UNIT_SIZE,
            unit_measures("f", 16),
            RiskBand.MODERATE,
            id="size-16-is-moderate",
        ),
        pytest.param(
            SystemProperty.UNIT_SIZE, unit_measures("f", 61), RiskBand.VERY_HIGH, id="size-61"
        ),
        pytest.param(
            SystemProperty.UNIT_INTERFACING,
            unit_measures("f", 1, parameter_count=2),
            RiskBand.LOW,
            id="two-parameters-is-low",
        ),
        pytest.param(
            SystemProperty.UNIT_INTERFACING,
            unit_measures("f", 1, parameter_count=3),
            RiskBand.MODERATE,
            id="three-parameters-is-moderate",
        ),
        pytest.param(
            SystemProperty.UNIT_INTERFACING,
            unit_measures("f", 1, parameter_count=7),
            RiskBand.VERY_HIGH,
            id="seven-parameters-is-very-high",
        ),
        pytest.param(
            SystemProperty.MODULE_COUPLING,
            file_measures("a.py", 1, fan_in=10),
            RiskBand.LOW,
            id="fan-in-10-is-low",
        ),
        pytest.param(
            SystemProperty.MODULE_COUPLING,
            file_measures("a.py", 1, fan_in=11),
            RiskBand.MODERATE,
            id="fan-in-11-is-moderate",
        ),
        pytest.param(
            SystemProperty.MODULE_COUPLING,
            file_measures("a.py", 1, fan_in=51),
            RiskBand.VERY_HIGH,
            id="fan-in-51-is-very-high",
        ),
    ],
)
def test_each_unit_or_file_lands_in_the_band_of_its_measure(
    system_property: SystemProperty, measures: list[Measure], expected_band: RiskBand
) -> None:
    profile = profile_of(measures, system_property)

    assert {band for band, lines in profile.lines_of_code_per_band.items() if lines} == {
        expected_band
    }


def test_module_coupling_profile_weighs_each_file_by_its_lines_of_code() -> None:
    measures = [
        *file_measures("hub.py", lines_of_code=300, fan_in=25),
        *file_measures("leaf.py", lines_of_code=100, fan_in=0),
    ]

    profile = profile_of(measures, SystemProperty.MODULE_COUPLING)

    assert profile.percentage_per_band == {
        RiskBand.LOW: 25.0,
        RiskBand.MODERATE: 0.0,
        RiskBand.HIGH: 75.0,
        RiskBand.VERY_HIGH: 0.0,
    }


def test_a_project_without_production_code_has_empty_profiles() -> None:
    profile = profile_of([], SystemProperty.UNIT_SIZE)

    assert sum(profile.lines_of_code_per_band.values()) == 0
    assert set(profile.percentage_per_band.values()) == {0.0}
