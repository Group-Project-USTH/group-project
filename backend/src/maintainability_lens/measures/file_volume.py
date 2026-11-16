from maintainability_lens.measures.parsed_file import ParsedFile
from maintainability_lens.schemas import Measure, MeasureName


def measure_file_volume(parsed_file: ParsedFile) -> Measure:
    return Measure(
        name=MeasureName.FILE_LINES_OF_CODE,
        value=len(parsed_file.code_lines),
        file=parsed_file.relative_file,
        line_start=1,
        line_end=max(parsed_file.line_count, 1),
    )
