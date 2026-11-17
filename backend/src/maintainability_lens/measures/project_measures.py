from collections.abc import Iterator
from pathlib import Path

from maintainability_lens.measures.cognitive_complexity import measure_cognitive_complexity
from maintainability_lens.measures.function_measures import measure_functions
from maintainability_lens.measures.python_units import PythonUnit, find_units
from maintainability_lens.measures.unit_interfacing import measure_unit_interfacing
from maintainability_lens.schemas import ProjectMeasures

NOT_PROJECT_FOLDERS = frozenset({"venv", "__pycache__", "node_modules", "site-packages"})


def is_project_folder(folder: str) -> bool:
    return not folder.startswith(".") and folder not in NOT_PROJECT_FOLDERS


def find_project_modules(target: Path) -> Iterator[Path]:
    for path in sorted(target.rglob("*.py")):
        folders = path.relative_to(target).parts[:-1]
        if all(is_project_folder(folder) for folder in folders):
            yield path


def find_units_if_parsable(path: Path) -> list[PythonUnit] | None:
    try:
        return find_units(path.read_text(encoding="utf-8"))
    except (SyntaxError, ValueError):
        return None


def measure_project(target: Path) -> ProjectMeasures:
    if not target.is_dir():
        raise NotADirectoryError(f"target is not a directory: {target}")
    measures = []
    unparsed_files = []
    for path in find_project_modules(target):
        relative_file = path.relative_to(target).as_posix()
        units = find_units_if_parsable(path)
        if units is None:
            unparsed_files.append(relative_file)
            continue
        measures.extend(measure_functions(path, relative_file, units))
        measures.extend(measure_cognitive_complexity(path, relative_file, units))
        measures.extend(measure_unit_interfacing(relative_file, units))
    return ProjectMeasures(measures=measures, unparsed_files=unparsed_files)
