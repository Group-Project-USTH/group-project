from pathlib import Path

import pytest

from maintainability_agent.measures import measure_project
from maintainability_agent.schemas import Measure, MeasureName


def write_module(root: Path, relative_path: str, source: str) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source)


def test_function_with_one_if_has_cyclomatic_complexity_two(tmp_path: Path) -> None:
    write_module(tmp_path, "app.py", "def f(x):\n    if x:\n        return 1\n    return 0\n")

    measures = measure_project(tmp_path).measures

    assert (
        Measure(
            name=MeasureName.CYCLOMATIC_COMPLEXITY,
            value=2,
            function="f",
            file="app.py",
            line_start=1,
            line_end=4,
        )
        in measures
    )


def measure_values(root: Path, name: MeasureName) -> dict[str, int]:
    return {
        measure.function: measure.value
        for measure in measure_project(root).measures
        if measure.name is name
    }


ELIF = (
    "def f(x):\n    if x == 1:\n        return 1\n"
    "    elif x == 2:\n        return 2\n    return 0\n"
)
EXCEPT = "def f(x):\n    try:\n        return int(x)\n    except ValueError:\n        return 0\n"
COMPREHENSION_FILTER = "def f(xs):\n    return [x for x in xs if x]\n"
ASSERT = "def f(x):\n    assert x\n    return x\n"
MATCH_TWO_CASES = (
    "def f(x):\n    match x:\n        case 1:\n            return 1\n"
    "        case _:\n            return 0\n"
)
BOOLEAN_OPERATORS = "def f(a, b, c):\n    return a and b or c\n"


@pytest.mark.parametrize(
    ("source", "expected_complexity"),
    [
        pytest.param(ELIF, 3, id="elif-adds-a-branch"),
        pytest.param(EXCEPT, 2, id="except-adds-a-branch"),
        pytest.param(COMPREHENSION_FILTER, 3, id="comprehension-loop-and-filter-add-branches"),
        pytest.param(ASSERT, 1, id="assert-is-not-a-branch"),
        pytest.param(MATCH_TWO_CASES, 3, id="each-match-case-adds-a-branch"),
        pytest.param(BOOLEAN_OPERATORS, 3, id="each-boolean-operator-adds-a-branch"),
    ],
)
def test_cyclomatic_complexity_follows_the_lizard_definition(
    tmp_path: Path, source: str, expected_complexity: int
) -> None:
    write_module(tmp_path, "app.py", source)

    assert measure_values(tmp_path, MeasureName.CYCLOMATIC_COMPLEXITY) == {"f": expected_complexity}


def test_code_outside_functions_has_no_cyclomatic_complexity(tmp_path: Path) -> None:
    write_module(tmp_path, "script.py", "import sys\nif sys.argv:\n    print(1)\n")

    assert measure_project(tmp_path).measures == []


def test_function_lines_of_code_skip_comments_and_blank_lines(tmp_path: Path) -> None:
    write_module(tmp_path, "app.py", "def f(x):\n    # explain\n\n    return x\n")

    assert measure_values(tmp_path, MeasureName.FUNCTION_LINES_OF_CODE) == {"f": 2}


def test_cognitive_complexity_adds_the_nesting_level(tmp_path: Path) -> None:
    write_module(
        tmp_path,
        "app.py",
        "def f(xs):\n    for x in xs:\n        if x:\n            print(x)\n",
    )

    assert measure_values(tmp_path, MeasureName.COGNITIVE_COMPLEXITY) == {"f": 3}


SAMPLE_PROJECT = Path(__file__).parents[1] / "fixtures" / "sample_project"


def test_sample_project_process_order_measures() -> None:
    process_order = {
        measure.name: measure
        for measure in measure_project(SAMPLE_PROJECT).measures
        if measure.function == "process_order"
    }

    assert {name: measure.value for name, measure in process_order.items()} == {
        MeasureName.CYCLOMATIC_COMPLEXITY: 7,
        MeasureName.COGNITIVE_COMPLEXITY: 8,
        MeasureName.FUNCTION_LINES_OF_CODE: 19,
    }
    assert {(m.file, m.line_start, m.line_end) for m in process_order.values()} == {
        ("app.py", 6, 25)
    }


def test_files_in_subfolders_are_cited_relative_to_the_target(tmp_path: Path) -> None:
    write_module(tmp_path, "shop/orders/checkout.py", "def pay():\n    return 1\n")

    assert {measure.file for measure in measure_project(tmp_path).measures} == {
        "shop/orders/checkout.py"
    }


@pytest.mark.parametrize("folder", [".venv", ".tox", "venv", "__pycache__", "node_modules"])
def test_tooling_and_hidden_folders_are_not_measured(tmp_path: Path, folder: str) -> None:
    write_module(tmp_path, "app.py", "def mine():\n    return 1\n")
    write_module(tmp_path, f"{folder}/lib/vendored.py", "def theirs():\n    return 1\n")

    assert {measure.function for measure in measure_project(tmp_path).measures} == {"mine"}


def test_unparsable_file_is_listed_and_the_rest_is_still_measured(tmp_path: Path) -> None:
    write_module(tmp_path, "good.py", "def fine():\n    return 1\n")
    write_module(tmp_path, "broken.py", "def broken(:\n    return 1\n")

    project_measures = measure_project(tmp_path)

    assert project_measures.unparsed_files == ["broken.py"]
    assert {measure.file for measure in project_measures.measures} == {"good.py"}
