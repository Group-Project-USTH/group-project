from pathlib import Path

import lizard

from maintainability_agent.schemas import Measure, MeasureName


def measure_functions(path: Path, relative_file: str) -> list[Measure]:
    analysed_file = lizard.analyze_file(str(path))
    return [
        Measure(
            name=name,
            value=value,
            function=function.name,
            file=relative_file,
            line_start=function.start_line,
            line_end=function.end_line,
        )
        for function in analysed_file.function_list
        for name, value in [
            (MeasureName.CYCLOMATIC_COMPLEXITY, function.cyclomatic_complexity),
            (MeasureName.FUNCTION_LINES_OF_CODE, function.nloc),
        ]
    ]
