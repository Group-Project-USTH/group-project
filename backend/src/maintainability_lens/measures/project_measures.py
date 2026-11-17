from collections.abc import Iterator
from pathlib import Path

from maintainability_lens.measures.cognitive_complexity import measure_cognitive_complexity
from maintainability_lens.measures.duplication import measure_duplication
from maintainability_lens.measures.file_volume import measure_file_volume
from maintainability_lens.measures.function_measures import measure_functions
from maintainability_lens.measures.module_coupling import measure_module_coupling
from maintainability_lens.measures.parsed_file import ParsedFile, parse_file
from maintainability_lens.measures.production_test_split import is_test_file
from maintainability_lens.measures.python_units import find_units
from maintainability_lens.measures.unit_interfacing import measure_unit_interfacing
from maintainability_lens.schemas import Measure, ProjectMeasures

NOT_PROJECT_FOLDERS = frozenset({"venv", "__pycache__", "node_modules", "site-packages"})


def is_project_folder(folder: str) -> bool:
    return not folder.startswith(".") and folder not in NOT_PROJECT_FOLDERS


def find_project_modules(target: Path) -> Iterator[Path]:
    for path in sorted(target.rglob("*.py")):
        folders = path.relative_to(target).parts[:-1]
        if all(is_project_folder(folder) for folder in folders):
            yield path


def measure_file(parsed_file: ParsedFile) -> list[Measure]:
    path, relative_file = parsed_file.path, parsed_file.relative_file
    units = find_units(parsed_file.tree)
    return [
        *measure_functions(path, relative_file, units),
        *measure_cognitive_complexity(path, relative_file, units),
        *measure_unit_interfacing(relative_file, units),
        measure_file_volume(parsed_file),
    ]


def measure_project(target: Path) -> ProjectMeasures:
    if not target.is_dir():
        raise NotADirectoryError(f"target is not a directory: {target}")
    parsed_files = []
    unparsed_files = []
    for path in find_project_modules(target):
        relative_file = path.relative_to(target).as_posix()
        parsed_file = parse_file(path, relative_file)
        if parsed_file is None:
            unparsed_files.append(relative_file)
        else:
            parsed_files.append(parsed_file)
    measures = [
        *(measure for parsed_file in parsed_files for measure in measure_file(parsed_file)),
        *measure_duplication(parsed_files),
        *measure_module_coupling(parsed_files, target.resolve().name),
    ]
    return ProjectMeasures(
        measures=[
            measure.model_copy(update={"is_test_code": is_test_file(measure.file)})
            for measure in measures
        ],
        unparsed_files=unparsed_files,
    )
