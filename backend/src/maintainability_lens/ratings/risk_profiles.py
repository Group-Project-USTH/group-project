from dataclasses import dataclass

from maintainability_lens.schemas import (
    Measure,
    MeasureName,
    ProjectMeasures,
    RiskBand,
    RiskProfile,
    SystemProperty,
)

BandLimits = tuple[int, int, int]
MeasureKey = tuple[str, str | None, int]

# Inclusive upper bounds of the low, moderate and high bands; anything above is very high.
# Heitlager, Kuipers and Visser 2007, p. 6 (the SEI McCabe categories), to match the 2007
# unit complexity Rating table.
UNIT_COMPLEXITY_BAND_LIMITS: BandLimits = (10, 20, 50)
# SIG/TÜV NORD CERT, Evaluation Criteria Trusted Product Maintainability: Guidance for
# Producers V18.1 (2026-03-31), section 3.
UNIT_SIZE_BAND_LIMITS: BandLimits = (15, 30, 60)
UNIT_INTERFACING_BAND_LIMITS: BandLimits = (2, 4, 6)
MODULE_COUPLING_BAND_LIMITS: BandLimits = (10, 20, 50)


@dataclass(frozen=True)
class RiskProfileRule:
    system_property: SystemProperty
    weight: MeasureName
    banded_by: MeasureName
    band_limits: BandLimits


RISK_PROFILE_RULES = (
    RiskProfileRule(
        SystemProperty.UNIT_SIZE,
        weight=MeasureName.FUNCTION_LINES_OF_CODE,
        banded_by=MeasureName.FUNCTION_LINES_OF_CODE,
        band_limits=UNIT_SIZE_BAND_LIMITS,
    ),
    RiskProfileRule(
        SystemProperty.UNIT_COMPLEXITY,
        weight=MeasureName.FUNCTION_LINES_OF_CODE,
        banded_by=MeasureName.CYCLOMATIC_COMPLEXITY,
        band_limits=UNIT_COMPLEXITY_BAND_LIMITS,
    ),
    RiskProfileRule(
        SystemProperty.UNIT_INTERFACING,
        weight=MeasureName.FUNCTION_LINES_OF_CODE,
        banded_by=MeasureName.PARAMETER_COUNT,
        band_limits=UNIT_INTERFACING_BAND_LIMITS,
    ),
    RiskProfileRule(
        SystemProperty.MODULE_COUPLING,
        weight=MeasureName.FILE_LINES_OF_CODE,
        banded_by=MeasureName.FILE_FAN_IN,
        band_limits=MODULE_COUPLING_BAND_LIMITS,
    ),
)


def band_of(value: int, band_limits: BandLimits) -> RiskBand:
    for band, limit in zip(
        (RiskBand.LOW, RiskBand.MODERATE, RiskBand.HIGH), band_limits, strict=True
    ):
        if value <= limit:
            return band
    return RiskBand.VERY_HIGH


def measure_key(measure: Measure) -> MeasureKey:
    return measure.file, measure.function, measure.line_start


def production_values(measures: list[Measure], name: MeasureName) -> dict[MeasureKey, int]:
    return {
        measure_key(measure): measure.value
        for measure in measures
        if measure.name is name and not measure.is_test_code
    }


def build_risk_profile(measures: list[Measure], rule: RiskProfileRule) -> RiskProfile:
    weights = production_values(measures, rule.weight)
    lines_of_code_per_band = dict.fromkeys(RiskBand, 0)
    for key, value in production_values(measures, rule.banded_by).items():
        lines_of_code_per_band[band_of(value, rule.band_limits)] += weights.get(key, 0)
    return RiskProfile(
        system_property=rule.system_property, lines_of_code_per_band=lines_of_code_per_band
    )


def build_risk_profiles(project_measures: ProjectMeasures) -> list[RiskProfile]:
    return [build_risk_profile(project_measures.measures, rule) for rule in RISK_PROFILE_RULES]
