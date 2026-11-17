from maintainability_lens.ratings.characteristic_ratings import rate_characteristics
from maintainability_lens.ratings.risk_profiles import build_risk_profiles
from maintainability_lens.ratings.system_property_ratings import (
    find_duplicated_percentage,
    rate_system_properties,
    total_of,
)
from maintainability_lens.schemas import Measure, MeasureName, ProjectMeasures, ProjectRatings

DEFAULT_FILE_LIMIT = 5


def find_top_production_files(
    project_measures: ProjectMeasures, name: MeasureName, file_limit: int
) -> list[Measure]:
    candidates = [
        measure
        for measure in project_measures.measures
        if measure.name is name and not measure.is_test_code and measure.value > 0
    ]
    return sorted(candidates, key=lambda measure: (-measure.value, measure.file))[:file_limit]


def rate_project(
    project_measures: ProjectMeasures, file_limit: int = DEFAULT_FILE_LIMIT
) -> ProjectRatings:
    system_property_ratings = rate_system_properties(project_measures)
    duplicated_percentage = find_duplicated_percentage(project_measures)
    return ProjectRatings(
        characteristic_ratings=rate_characteristics(system_property_ratings),
        system_property_ratings=system_property_ratings,
        risk_profiles=build_risk_profiles(project_measures),
        production_lines_of_code=total_of(
            project_measures, MeasureName.FILE_LINES_OF_CODE, is_test_code=False
        ),
        test_lines_of_code=total_of(
            project_measures, MeasureName.FILE_LINES_OF_CODE, is_test_code=True
        ),
        duplicated_percentage=(
            None if duplicated_percentage is None else round(float(duplicated_percentage), 1)
        ),
        most_duplicated_files=find_top_production_files(
            project_measures, MeasureName.DUPLICATED_LINES, file_limit
        ),
        highest_fan_in_files=find_top_production_files(
            project_measures, MeasureName.FILE_FAN_IN, file_limit
        ),
        unparsed_files=project_measures.unparsed_files,
    )
