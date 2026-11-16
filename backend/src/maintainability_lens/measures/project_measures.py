import ast
from collections.abc import Iterator
from pathlib import Path

from maintainability_lens.measures.cognitive_complexity import measure_cognitive_complexity
from maintainability_lens.measures.file_volume import measure_file_volume
from maintainability_lens.measures.function_measures import measure_functions
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


def parse_if_possible(source: str) -> ast.Module | None:
    try:
        return ast.parse(source)
    except (SyntaxError, ValueError):
        return None


def measure_file(path: Path, relative_file: str, source: str, tree: ast.Module) -> list[Measure]:
    units = find_units(tree)
    return [
        *measure_functions(path, relative_file, units),
        *measure_cognitive_complexity(path, relative_file, units),
        *measure_unit_interfacing(relative_file, units),
        measure_file_volume(relative_file, source, tree),
    ]


def measure_project(target: Path) -> ProjectMeasures:
    if not target.is_dir():
        raise NotADirectoryError(f"target is not a directory: {target}")
    measures: list[Measure] = []
    unparsed_files = []
    for path in find_project_modules(target):
        relative_file = path.relative_to(target).as_posix()
        source = path.read_text(encoding="utf-8")
        tree = parse_if_possible(source)
        if tree is None:
            unparsed_files.append(relative_file)
            continue
        is_test_code = is_test_file(relative_file)
        measures.extend(
            measure.model_copy(update={"is_test_code": is_test_code})
            for measure in measure_file(path, relative_file, source, tree)
        )
    return ProjectMeasures(measures=measures, unparsed_files=unparsed_files)
