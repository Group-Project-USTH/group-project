from functools import lru_cache
from pathlib import Path

from maintainability_lens.measures import measure_project, scope_to_file
from maintainability_lens.schemas import ProjectMeasures

measure_checkout = lru_cache(maxsize=8)(measure_project)


def measure_file_in_project(checkout: Path, file: str) -> ProjectMeasures:
    return scope_to_file(measure_checkout(checkout), file)
