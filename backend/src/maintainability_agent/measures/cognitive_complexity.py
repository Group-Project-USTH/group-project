from pathlib import Path

import complexipy

from maintainability_agent.schemas import Measure, MeasureName


def measure_cognitive_complexity(path: Path, relative_file: str) -> list[Measure]:
    return [
        Measure(
            name=MeasureName.COGNITIVE_COMPLEXITY,
            value=function.complexity,
            function=function.name,
            file=relative_file,
            line_start=function.line_start,
            line_end=function.line_end,
        )
        for function in complexipy.file_complexity(str(path)).functions
    ]
