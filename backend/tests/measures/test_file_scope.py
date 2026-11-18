from pathlib import Path

import pytest

from maintainability_lens.measures import measure_project, scope_to_file
from maintainability_lens.schemas import MeasureName

REPEATED_BLOCK = "".join(f"    total = total + {index}\n" for index in range(6))


def write_module(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)


def test_scope_keeps_only_the_measures_of_the_chosen_file(tmp_path: Path) -> None:
    write_module(tmp_path, "pkg/__init__.py", "")
    write_module(tmp_path, "pkg/core.py", "def f(x):\n    return x\n")
    write_module(tmp_path, "pkg/other.py", "def g(x):\n    return x\n")

    scoped = scope_to_file(measure_project(tmp_path), "pkg/core.py")

    assert {measure.file for measure in scoped.measures} == {"pkg/core.py"}
    assert {measure.function for measure in scoped.measures} == {"f", None}


def test_scope_keeps_fan_in_counted_from_the_rest_of_the_project(tmp_path: Path) -> None:
    write_module(tmp_path, "core.py", "def f(x):\n    return x\n")
    write_module(tmp_path, "first.py", "import core\n")
    write_module(tmp_path, "second.py", "from core import f\n")

    scoped = scope_to_file(measure_project(tmp_path), "core.py")

    fan_in = [measure for measure in scoped.measures if measure.name is MeasureName.FILE_FAN_IN]
    assert [measure.value for measure in fan_in] == [2]


def test_scope_keeps_duplication_found_against_other_files(tmp_path: Path) -> None:
    source = f"def f():\n    total = 0\n{REPEATED_BLOCK}    return total\n"
    write_module(tmp_path, "first.py", source)
    write_module(tmp_path, "second.py", source.replace("def f", "def g"))

    scoped = scope_to_file(measure_project(tmp_path), "first.py")

    duplicated = [
        measure for measure in scoped.measures if measure.name is MeasureName.DUPLICATED_LINES
    ]
    assert [measure.value for measure in duplicated] == [8]


def test_scope_to_an_unparsed_file_keeps_it_as_unparsed(tmp_path: Path) -> None:
    write_module(tmp_path, "broken.py", "def f(:\n")
    write_module(tmp_path, "fine.py", "def g(x):\n    return x\n")

    scoped = scope_to_file(measure_project(tmp_path), "broken.py")

    assert scoped.measures == []
    assert scoped.unparsed_files == ["broken.py"]


def test_scope_to_a_file_outside_the_project_is_rejected(tmp_path: Path) -> None:
    write_module(tmp_path, "fine.py", "def g(x):\n    return x\n")

    with pytest.raises(ValueError, match=r"missing\.py"):
        scope_to_file(measure_project(tmp_path), "missing.py")
