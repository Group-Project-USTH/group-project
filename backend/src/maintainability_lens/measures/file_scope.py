from maintainability_lens.schemas import ProjectMeasures


def scope_to_file(project_measures: ProjectMeasures, file: str) -> ProjectMeasures:
    measures = [measure for measure in project_measures.measures if measure.file == file]
    unparsed_files = [unparsed for unparsed in project_measures.unparsed_files if unparsed == file]
    if not measures and not unparsed_files:
        raise ValueError(f"not a Python file of the project: {file}")
    return ProjectMeasures(measures=measures, unparsed_files=unparsed_files)
