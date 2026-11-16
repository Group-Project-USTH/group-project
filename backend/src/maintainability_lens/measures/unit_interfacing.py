from maintainability_lens.measures.python_units import PythonUnit
from maintainability_lens.schemas import Measure, MeasureName


def measure_unit_interfacing(relative_file: str, units: list[PythonUnit]) -> list[Measure]:
    return [
        Measure(
            name=MeasureName.PARAMETER_COUNT,
            value=unit.parameter_count,
            function=unit.qualified_name,
            file=relative_file,
            line_start=unit.line_start,
            line_end=unit.line_end,
        )
        for unit in units
    ]
