import lizard

from maintainability_lens.measures.python_units import PythonUnit
from maintainability_lens.schemas import Measure, MeasureName


def measure_functions(source: str, relative_file: str, units: list[PythonUnit]) -> list[Measure]:
    units_by_def_line = {unit.line_start: unit for unit in units}
    return [
        Measure(
            name=name,
            value=value,
            function=unit.qualified_name,
            file=relative_file,
            line_start=unit.line_start,
            line_end=unit.line_end,
        )
        for function in lizard.analyze_file.analyze_source_code(relative_file, source).function_list
        if (unit := units_by_def_line.get(function.start_line))
        for name, value in [
            (MeasureName.CYCLOMATIC_COMPLEXITY, function.cyclomatic_complexity),
            (MeasureName.FUNCTION_LINES_OF_CODE, function.nloc),
        ]
    ]
