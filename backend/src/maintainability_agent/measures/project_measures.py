import ast
from collections.abc import Iterator
from pathlib import Path

from maintainability_agent.measures.cognitive_complexity import measure_cognitive_complexity
from maintainability_agent.measures.function_measures import measure_functions
from maintainability_agent.schemas import ProjectMeasures

NOT_PROJECT_FOLDERS = frozenset({"venv", "__pycache__", "node_modules", "site-packages"})


def is_project_folder(folder: str) -> bool:
    return not folder.startswith(".") and folder not in NOT_PROJECT_FOLDERS


def find_project_modules(target: Path) -> Iterator[Path]:
    for path in sorted(target.rglob("*.py")):
        folders = path.relative_to(target).parts[:-1]
        if all(is_project_folder(folder) for folder in folders):
            yield path


def is_parsable(path: Path) -> bool:
    try:
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (SyntaxError, ValueError):
        return False
    return True


def measure_project(target: Path) -> ProjectMeasures:
    if not target.is_dir():
        raise NotADirectoryError(f"target is not a directory: {target}")
    measures = []
    unparsed_files = []
    for path in find_project_modules(target):
        relative_file = path.relative_to(target).as_posix()
        if not is_parsable(path):
            unparsed_files.append(relative_file)
            continue
        measures.extend(measure_functions(path, relative_file))
        measures.extend(measure_cognitive_complexity(path, relative_file))
    return ProjectMeasures(measures=measures, unparsed_files=unparsed_files)
