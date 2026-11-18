import complexipy

from maintainability_lens.measures.python_units import PythonUnit
from maintainability_lens.schemas import Measure, MeasureName


def measure_cognitive_complexity(
    source: str, relative_file: str, units: list[PythonUnit]
) -> list[Measure]:
    # complexipy starts a unit at its first decorator, lizard at its `def` line.
    units_by_first_line = {unit.first_line_with_decorators: unit for unit in units}
    return [
        Measure(
            name=MeasureName.COGNITIVE_COMPLEXITY,
            value=function.complexity,
            function=unit.qualified_name,
            file=relative_file,
            line_start=unit.line_start,
            line_end=unit.line_end,
        )
        for function in complexipy.code_complexity(source).functions
        if (unit := units_by_first_line.get(function.line_start))
    ]
