from maintainability_lens.schemas import (
    Measure,
    MeasureName,
    ProjectMeasures,
    ProjectMeasureSummary,
)


def function_location(measure: Measure) -> tuple[str, str | None, int]:
    return measure.file, measure.function, measure.line_start


def summarise_worst_functions(
    project_measures: ProjectMeasures, function_limit: int
) -> ProjectMeasureSummary:
    complexities = [
        measure
        for measure in project_measures.measures
        if measure.name is MeasureName.CYCLOMATIC_COMPLEXITY
    ]
    worst = sorted(complexities, key=lambda measure: measure.value, reverse=True)[:function_limit]
    worst_locations = {function_location(measure) for measure in worst}
    return ProjectMeasureSummary(
        measures=[
            measure
            for measure in project_measures.measures
            if function_location(measure) in worst_locations
        ],
        function_count=len(complexities),
        unparsed_files=project_measures.unparsed_files,
    )
